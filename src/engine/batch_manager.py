from typing import List, Dict, Any, Generator, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
import math

from ..config.settings import Settings
from ..config.logging_config import get_logger


@dataclass
class BatchInfo:
    """Information about a processing batch"""
    batch_id: str
    batch_number: int
    total_batches: int
    start_index: int
    end_index: int
    size: int
    total_records: int
    created_at: datetime


class BatchManager:
    """Manages batch processing of large datasets"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.default_batch_size = settings.batch_size
    
    def create_batches(
        self,
        data: List[Any],
        batch_size: Optional[int] = None,
        max_batches: Optional[int] = None
    ) -> Generator[BatchInfo, None, None]:
        """Create batch information for processing data"""
        batch_size = batch_size or self.default_batch_size
        total_records = len(data)
        total_batches = math.ceil(total_records / batch_size)
        
        if max_batches:
            total_batches = min(total_batches, max_batches)
        
        self.logger.info(f"Creating {total_batches} batches of size {batch_size} for {total_records} records")
        
        for batch_number in range(total_batches):
            start_index = batch_number * batch_size
            end_index = min(start_index + batch_size, total_records)
            current_batch_size = end_index - start_index
            
            if current_batch_size <= 0:
                break
            
            batch_info = BatchInfo(
                batch_id=str(uuid.uuid4()),
                batch_number=batch_number + 1,
                total_batches=total_batches,
                start_index=start_index,
                end_index=end_index,
                size=current_batch_size,
                total_records=total_records,
                created_at=datetime.utcnow()
            )
            
            yield batch_info
    
    def get_batch_data(self, data: List[Any], batch_info: BatchInfo) -> List[Any]:
        """Extract data for a specific batch"""
        return data[batch_info.start_index:batch_info.end_index]
    
    def calculate_optimal_batch_size(
        self,
        total_records: int,
        max_concurrent: Optional[int] = None,
        memory_per_record: int = 1024  # bytes
    ) -> int:
        """Calculate optimal batch size based on system constraints"""
        max_concurrent = max_concurrent or self.settings.max_concurrent_requests
        
        # Estimate memory requirements
        max_memory_per_batch = 100 * 1024 * 1024  # 100MB
        memory_based_batch_size = max_memory_per_batch // memory_per_record
        
        # Calculate based on concurrency
        concurrency_based_batch_size = max(1, total_records // max_concurrent)
        
        # Use the smaller of the two, but not less than 1
        optimal_batch_size = max(1, min(memory_based_batch_size, concurrency_based_batch_size))
        
        # Ensure it's reasonable (not too small or too large)
        optimal_batch_size = max(10, min(optimal_batch_size, 1000))
        
        self.logger.info(
            f"Calculated optimal batch size: {optimal_batch_size} "
            f"(memory: {memory_based_batch_size}, concurrency: {concurrency_based_batch_size})"
        )
        
        return int(optimal_batch_size)
    
    def create_progress_tracker(self, total_records: int, batch_size: int) -> Dict[str, Any]:
        """Create a progress tracker for batch processing"""
        total_batches = math.ceil(total_records / batch_size)
        
        return {
            'total_records': total_records,
            'total_batches': total_batches,
            'batch_size': batch_size,
            'processed_records': 0,
            'processed_batches': 0,
            'success_count': 0,
            'failed_count': 0,
            'start_time': datetime.utcnow(),
            'last_update': datetime.utcnow(),
            'batches': {}  # Track individual batch status
        }
    
    def update_progress(
        self,
        progress_tracker: Dict[str, Any],
        batch_info: BatchInfo,
        success_count: int,
        failed_count: int
    ) -> Dict[str, Any]:
        """Update progress tracker with batch results"""
        # Update batch status
        progress_tracker['batches'][batch_info.batch_id] = {
            'batch_number': batch_info.batch_number,
            'status': 'completed' if failed_count == 0 else 'partial' if success_count > 0 else 'failed',
            'success_count': success_count,
            'failed_count': failed_count,
            'processed_at': datetime.utcnow()
        }
        
        # Update overall progress
        progress_tracker['processed_records'] += batch_info.size
        progress_tracker['processed_batches'] += 1
        progress_tracker['success_count'] += success_count
        progress_tracker['failed_count'] += failed_count
        progress_tracker['last_update'] = datetime.utcnow()
        
        return progress_tracker
    
    def get_progress_summary(self, progress_tracker: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of current progress"""
        total_records = progress_tracker['total_records']
        processed_records = progress_tracker['processed_records']
        success_count = progress_tracker['success_count']
        failed_count = progress_tracker['failed_count']
        
        completion_percentage = (processed_records / total_records * 100) if total_records > 0 else 0
        success_rate = (success_count / processed_records * 100) if processed_records > 0 else 0
        
        # Calculate estimated time remaining
        elapsed_time = (datetime.utcnow() - progress_tracker['start_time']).total_seconds()
        records_per_second = processed_records / elapsed_time if elapsed_time > 0 else 0
        estimated_remaining = (total_records - processed_records) / records_per_second if records_per_second > 0 else 0
        
        return {
            'completion_percentage': round(completion_percentage, 2),
            'success_rate': round(success_rate, 2),
            'processed_records': processed_records,
            'total_records': total_records,
            'success_count': success_count,
            'failed_count': failed_count,
            'processed_batches': progress_tracker['processed_batches'],
            'total_batches': progress_tracker['total_batches'],
            'elapsed_seconds': round(elapsed_time, 2),
            'estimated_remaining_seconds': round(estimated_remaining, 2),
            'records_per_second': round(records_per_second, 2)
        }
    
    def should_process_batch(
        self,
        batch_info: BatchInfo,
        retry_threshold: int = 3
    ) -> bool:
        """Determine if a batch should be processed based on retry logic"""
        # This method would typically check against a database of failed batches
        # For now, we'll always process new batches
        return True
    
    def get_batch_statistics(self, batches: List[BatchInfo]) -> Dict[str, Any]:
        """Get statistics about batch processing"""
        if not batches:
            return {
                'total_batches': 0,
                'total_records': 0,
                'average_batch_size': 0,
                'min_batch_size': 0,
                'max_batch_size': 0
            }
        
        batch_sizes = [batch.size for batch in batches]
        total_records = sum(batch_sizes)
        
        return {
            'total_batches': len(batches),
            'total_records': total_records,
            'average_batch_size': round(sum(batch_sizes) / len(batch_sizes), 2),
            'min_batch_size': min(batch_sizes),
            'max_batch_size': max(batch_sizes),
            'batch_size_distribution': self._get_batch_size_distribution(batch_sizes)
        }
    
    def _get_batch_size_distribution(self, batch_sizes: List[int]) -> Dict[str, int]:
        """Get distribution of batch sizes"""
        distribution = {}
        for size in sorted(set(batch_sizes)):
            distribution[size] = batch_sizes.count(size)
        return distribution
    
    def validate_batch_config(self, batch_size: int, total_records: int) -> Dict[str, Any]:
        """Validate batch configuration"""
        issues = []
        
        if batch_size <= 0:
            issues.append("Batch size must be positive")
        
        if batch_size > total_records and total_records > 0:
            issues.append("Batch size cannot exceed total records")
        
        if batch_size > 10000:
            issues.append("Batch size is unusually large (> 10,000)")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recommended_batch_size': self.calculate_optimal_batch_size(total_records) if total_records > 0 else 100
        }