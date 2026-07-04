import asyncio
import uuid
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import aiohttp
from sqlalchemy.orm import Session
import pandas as pd
from tqdm import tqdm
import json

from ..api.base_client import BaseAPIClient
from ..api.apple_client import AppleBusinessConnectClient
from ..api.yext_client import YextClient
from ..api.uberall_client import UberallClient
from ..api.rio_seo_client import RioSeoClient
from ..data.schema import BulkUploadRequest, BulkUploadResponse
from ..data.reader import DataReader
from ..data.processor import DataProcessor
from ..data.validator import DataValidator
from ..data.transformer import DataTransformer, AggregatorType
from ..storage.database import get_db_manager
from ..storage.models import Location, SyncJob, LocationStatus, SyncJobStatus
from ..storage.queue import FailedRecordQueue
from ..storage.cache import StatusCache
from ..config.settings import Settings
from ..config.logging_config import get_logger


class BulkUploader:
    """Main bulk upload engine for processing location data"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize components
        self.db_manager = get_db_manager(settings)
        self.data_reader = DataReader()
        self.data_processor = DataProcessor()
        self.data_validator = DataValidator()
        self.data_transformer = DataTransformer()
        self.failed_queue = FailedRecordQueue(settings)
        self.status_cache = StatusCache(settings)
        
        # Initialize API clients
        self.api_clients = {
            'apple': AppleBusinessConnectClient(settings),
            'yext': YextClient(settings),
            'uberall': UberallClient(settings),
            'rio_seo': RioSeoClient(settings)
        }
        
        # Progress tracking
        self.progress_callbacks: List[Callable] = []
    
    def add_progress_callback(self, callback: Callable):
        """Add callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, progress_data: Dict[str, Any]):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {str(e)}")
    
    async def upload_from_file(
        self,
        file_path: str,
        aggregator: str,
        batch_size: Optional[int] = None,
        validate_only: bool = False,
        dry_run: bool = False
    ) -> BulkUploadResponse:
        """Upload locations from file"""
        batch_size = batch_size or self.settings.batch_size
        batch_id = str(uuid.uuid4())
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Read data
            self.logger.info(f"Starting bulk upload from {file_path} to {aggregator}")
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'reading',
                'message': 'Reading input file',
                'progress': 0
            })
            
            raw_data = self.data_reader.read_file(file_path)
            
            # Convert to list of dictionaries if it's a DataFrame
            if isinstance(raw_data, pd.DataFrame):
                locations_data = raw_data.to_dict('records')
            else:
                locations_data = raw_data
            
            total_records = len(locations_data)
            
            # Step 2: Process data
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'processing',
                'message': 'Processing location data',
                'progress': 10,
                'total_records': total_records
            })
            
            processed_locations = self.data_processor.process_dataframe(
                pd.DataFrame(locations_data) if isinstance(raw_data, list) else raw_data,
                source_type='file'
            )
            
            # Step 3: Validate data
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'validating',
                'message': 'Validating location data',
                'progress': 30
            })
            
            valid_locations, validation_errors = self.data_validator.validate_locations(processed_locations)
            
            if validate_only:
                # Return validation results without uploading
                return BulkUploadResponse(
                    batch_id=batch_id,
                    total_records=total_records,
                    valid_records=len(valid_locations),
                    invalid_records=len(validation_errors),
                    validation_errors=[err.model_dump() for err in validation_errors],
                    started_at=start_time,
                    completed_at=datetime.utcnow(),
                    status='validation_complete'
                )
            
            # Step 4: Transform for target aggregator
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'transforming',
                'message': f'Transforming data for {aggregator}',
                'progress': 50
            })
            
            try:
                aggregator_type = AggregatorType(aggregator)
                transformed_locations = self.data_transformer.transform_batch_to_aggregator_format(
                    valid_locations, aggregator_type
                )
            except ValueError as e:
                raise ValueError(f"Unsupported aggregator {aggregator}: {str(e)}")
            
            # Step 5: Upload data
            if not dry_run:
                self._notify_progress({
                    'batch_id': batch_id,
                    'status': 'uploading',
                    'message': f'Uploading to {aggregator}',
                    'progress': 70
                })
                
                upload_results = await self._upload_batch(
                    transformed_locations, aggregator, batch_size, batch_id
                )
            else:
                # Dry run - simulate upload
                upload_results = {
                    'success_count': len(transformed_locations),
                    'failed_count': 0,
                    'failed_records': []
                }
                await asyncio.sleep(1)  # Simulate processing time
            
            # Step 6: Complete
            completed_at = datetime.utcnow()
            
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'completed',
                'message': 'Upload completed successfully',
                'progress': 100,
                'success_count': upload_results['success_count'],
                'failed_count': upload_results['failed_count']
            })
            
            self.logger.info(
                f"Bulk upload completed: {upload_results['success_count']} success, "
                f"{upload_results['failed_count']} failed"
            )
            
            return BulkUploadResponse(
                batch_id=batch_id,
                total_records=total_records,
                valid_records=len(valid_locations),
                invalid_records=len(validation_errors),
                validation_errors=[err.model_dump() for err in validation_errors],
                started_at=start_time,
                completed_at=completed_at,
                status='completed'
            )
            
        except Exception as e:
            self.logger.error(f"Bulk upload failed: {str(e)}")
            self._notify_progress({
                'batch_id': batch_id,
                'status': 'failed',
                'message': f'Upload failed: {str(e)}',
                'progress': 100,
                'error': str(e)
            })
            raise
    
    async def _upload_batch(
        self,
        locations: List[Dict[str, Any]],
        aggregator: str,
        batch_size: int,
        batch_id: str
    ) -> Dict[str, Any]:
        """Upload locations in batches"""
        client = self.api_clients.get(aggregator)
        if not client:
            raise ValueError(f"Unsupported aggregator: {aggregator}")
        
        success_count = 0
        failed_count = 0
        failed_records = []
        
        # Process in batches
        for i in range(0, len(locations), batch_size):
            batch = locations[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(locations) + batch_size - 1) // batch_size
            
            self.logger.info(f"Processing batch {batch_number}/{total_batches} ({len(batch)} locations)")
            
            # Update batch status in cache
            await self.status_cache.set_batch_status(
                batch_id,
                'uploading',
                progress=(i / len(locations)) * 100,
                total=len(locations),
                completed=success_count,
                failed=failed_count
            )
            
            try:
                # Upload batch
                if len(batch) == 1:
                    # Single location upload
                    result = await self._upload_single_location(client, batch[0], aggregator)
                else:
                    # Bulk upload
                    result = await self._upload_bulk_locations(client, batch, aggregator)
                
                success_count += result['success_count']
                failed_count += result['failed_count']
                failed_records.extend(result['failed_records'])
                
            except Exception as e:
                self.logger.error(f"Batch {batch_number} failed: {str(e)}")
                failed_count += len(batch)
                failed_records.extend([
                    {
                        'location_id': loc.get('external_id') or loc.get('id') or f"batch_{batch_number}_item_{j}",
                        'error': str(e),
                        'data': loc
                    }
                    for j, loc in enumerate(batch)
                ])
        
        # Store failed records in database
        if failed_records:
            await self._store_failed_records(failed_records, aggregator)
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_records': failed_records
        }
    
    async def _upload_single_location(
        self,
        client: BaseAPIClient,
        location: Dict[str, Any],
        aggregator: str
    ) -> Dict[str, Any]:
        """Upload a single location"""
        try:
            response = client.create_location(location)
            
            if response.status_code in [200, 201]:
                return {
                    'success_count': 1,
                    'failed_count': 0,
                    'failed_records': []
                }
            else:
                return {
                    'success_count': 0,
                    'failed_count': 1,
                    'failed_records': [{
                        'location_id': location.get('external_id') or location.get('id') or 'unknown',
                        'error': f"HTTP {response.status_code}: {response.data}",
                        'data': location
                    }]
                }
                
        except Exception as e:
            return {
                'success_count': 0,
                'failed_count': 1,
                'failed_records': [{
                    'location_id': location.get('external_id') or location.get('id') or 'unknown',
                    'error': str(e),
                    'data': location
                }]
            }
    
    async def _upload_bulk_locations(
        self,
        client: BaseAPIClient,
        locations: List[Dict[str, Any]],
        aggregator: str
    ) -> Dict[str, Any]:
        """Upload multiple locations in bulk"""
        try:
            response = client.create_locations_bulk(locations)
            
            if response.status_code in [200, 201]:
                return {
                    'success_count': len(locations),
                    'failed_count': 0,
                    'failed_records': []
                }
            else:
                # Handle partial failures
                return {
                    'success_count': 0,
                    'failed_count': len(locations),
                    'failed_records': [{
                        'location_id': loc.get('external_id') or loc.get('id') or f"bulk_item_{i}",
                        'error': f"HTTP {response.status_code}: {response.data}",
                        'data': loc
                    } for i, loc in enumerate(locations)]
                }
                
        except Exception as e:
            return {
                'success_count': 0,
                'failed_count': len(locations),
                'failed_records': [{
                    'location_id': loc.get('external_id') or loc.get('id') or f"bulk_item_{i}",
                    'error': str(e),
                    'data': loc
                } for i, loc in enumerate(locations)]
            }
    
    async def _store_failed_records(self, failed_records: List[Dict[str, Any]], aggregator: str):
        """Store failed records in the database"""
        with self.db_manager.get_sync_session() as session:
            for record in failed_records:
                self.failed_queue.add_failed_record(
                    session=session,
                    location_id=record['location_id'],
                    error_type='upload_failed',
                    error_message=record['error'],
                    error_details={'aggregator': aggregator},
                    raw_data=record['data']
                )
            session.commit()
    
    async def retry_failed_records(self, max_records: int = 100) -> Dict[str, Any]:
        """Retry failed records from the queue"""
        self.logger.info("Starting retry of failed records")
        
        with self.db_manager.get_sync_session() as session:
            pending_records = self.failed_queue.get_pending_records(session, limit=max_records)
            
            if not pending_records:
                self.logger.info("No pending failed records to retry")
                return {'processed': 0, 'success': 0, 'failed': 0}
            
            success_count = 0
            failed_count = 0
            
            for record in pending_records:
                try:
                    # Determine which aggregator to use
                    error_details = record.error_details or {}
                    aggregator = error_details.get('aggregator', 'apple')
                    
                    # Get API client
                    client = self.api_clients.get(aggregator)
                    if not client:
                        raise ValueError(f"Unsupported aggregator: {aggregator}")
                    
                    # Retry upload
                    if record.raw_data:
                        result = await self._upload_single_location(client, record.raw_data, aggregator)
                        
                        if result['success_count'] > 0:
                            # Mark as resolved
                            self.failed_queue.mark_as_resolved(session, record.id)
                            success_count += 1
                        else:
                            # Increment retry count
                            self.failed_queue.increment_retry_count(session, record.id, result['failed_records'][0]['error'])
                            failed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to retry record {record.id}: {str(e)}")
                    try:
                        self.failed_queue.increment_retry_count(session, record.id, str(e))
                    except Exception as inner_e:
                        self.logger.error(f"Failed to update retry count for record {record.id}: {str(inner_e)}")
                    failed_count += 1
            
            session.commit()
            
            self.logger.info(f"Retry completed: {success_count} success, {failed_count} failed")
            return {
                'processed': len(pending_records),
                'success': success_count,
                'failed': failed_count
            }
    
    def close(self):
        """Clean up resources"""
        for client in self.api_clients.values():
            client.close()
        self.db_manager.close()