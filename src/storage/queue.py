from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import json

from .models import FailedRecord, Location, FailedRecord
from ..config.settings import Settings


class FailedRecordQueue:
    """Manages the queue of failed records for retry processing"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.max_retries = settings.retry_max_attempts
    
    def add_failed_record(
        self,
        session: Session,
        location_id: str,
        error_type: str,
        error_message: str,
        error_code: Optional[str] = None,
        error_details: Optional[dict] = None,
        raw_data: Optional[dict] = None,
        max_retries: Optional[int] = None
    ) -> FailedRecord:
        """Add a failed record to the queue"""
        failed_record = FailedRecord(
            location_id=location_id,
            error_type=error_type,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            raw_data=raw_data,
            max_retries=max_retries or self.max_retries,
            retry_count=0,
            next_retry_at=self._calculate_next_retry(0)
        )
        
        session.add(failed_record)
        session.flush()
        return failed_record
    
    def get_pending_records(
        self,
        session: Session,
        limit: int = 100,
        max_retries: Optional[int] = None
    ) -> List[FailedRecord]:
        """Get pending failed records ready for retry"""
        max_retries = max_retries or self.max_retries
        
        query = session.query(FailedRecord).filter(
            and_(
                FailedRecord.resolved == False,
                FailedRecord.retry_count < max_retries,
                or_(
                    FailedRecord.next_retry_at == None,
                    FailedRecord.next_retry_at <= datetime.utcnow()
                )
            )
        ).order_by(FailedRecord.created_at.asc()).limit(limit)
        
        return query.all()
    
    def increment_retry_count(
        self,
        session: Session,
        failed_record_id: int,
        error_message: Optional[str] = None
    ) -> FailedRecord:
        """Increment retry count for a failed record"""
        failed_record = session.query(FailedRecord).get(failed_record_id)
        if not failed_record:
            raise ValueError(f"Failed record {failed_record_id} not found")
        
        failed_record.retry_count += 1
        failed_record.next_retry_at = self._calculate_next_retry(failed_record.retry_count)
        
        if error_message:
            failed_record.error_message = error_message
        
        session.add(failed_record)
        return failed_record
    
    def mark_as_resolved(
        self,
        session: Session,
        failed_record_id: int
    ) -> FailedRecord:
        """Mark a failed record as resolved"""
        failed_record = session.query(FailedRecord).get(failed_record_id)
        if not failed_record:
            raise ValueError(f"Failed record {failed_record_id} not found")
        
        failed_record.resolved = True
        failed_record.resolved_at = datetime.utcnow()
        
        session.add(failed_record)
        return failed_record
    
    def get_failed_records_by_location(
        self,
        session: Session,
        location_id: str
    ) -> List[FailedRecord]:
        """Get all failed records for a specific location"""
        return session.query(FailedRecord).filter(
            FailedRecord.location_id == location_id
        ).order_by(FailedRecord.created_at.desc()).all()
    
    def get_failed_records_by_error_type(
        self,
        session: Session,
        error_type: str,
        limit: int = 100
    ) -> List[FailedRecord]:
        """Get failed records by error type"""
        return session.query(FailedRecord).filter(
            FailedRecord.error_type == error_type
        ).order_by(FailedRecord.created_at.desc()).limit(limit).all()
    
    def get_retry_statistics(self, session: Session) -> dict:
        """Get statistics about failed records and retries"""
        total_failed = session.query(FailedRecord).count()
        pending_retries = session.query(FailedRecord).filter(
            and_(
                FailedRecord.resolved == False,
                FailedRecord.retry_count < FailedRecord.max_retries
            )
        ).count()
        
        resolved = session.query(FailedRecord).filter(
            FailedRecord.resolved == True
        ).count()
        
        permanently_failed = session.query(FailedRecord).filter(
            and_(
                FailedRecord.resolved == False,
                FailedRecord.retry_count >= FailedRecord.max_retries
            )
        ).count()
        
        return {
            "total_failed": total_failed,
            "pending_retries": pending_retries,
            "resolved": resolved,
            "permanently_failed": permanently_failed,
            "success_rate": (resolved / total_failed * 100) if total_failed > 0 else 0
        }
    
    def _calculate_next_retry(self, retry_count: int) -> datetime:
        """Calculate next retry time with exponential backoff"""
        if retry_count == 0:
            return datetime.utcnow()
        
        backoff_seconds = (
            self.settings.retry_backoff_factor ** retry_count
        ) * 60  # Convert to minutes
        
        return datetime.utcnow() + timedelta(seconds=backoff_seconds)
    
    def cleanup_old_records(
        self,
        session: Session,
        days_old: int = 30
    ) -> int:
        """Clean up old resolved failed records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = session.query(FailedRecord).filter(
            and_(
                FailedRecord.resolved == True,
                FailedRecord.resolved_at < cutoff_date
            )
        ).delete()
        
        return deleted_count