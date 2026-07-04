from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
import re
from datetime import datetime


class LocationStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class BusinessHoursSlot(BaseModel):
    """Represents a single time slot for business hours"""
    opens: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    closes: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    @field_validator('closes')
    @classmethod
    def validate_closing_time(cls, v: str, info) -> str:
        if 'opens' in info.data:
            opens_time = info.data['opens']
            opens_hours, opens_minutes = map(int, opens_time.split(':'))
            closes_hours, closes_minutes = map(int, v.split(':'))
            
            opens_total = opens_hours * 60 + opens_minutes
            closes_total = closes_hours * 60 + closes_minutes
            
            if closes_total <= opens_total:
                raise ValueError("Closing time must be after opening time")
        
        return v


class BusinessHours(BaseModel):
    """Business hours for each day of the week"""
    monday: Optional[List[BusinessHoursSlot]] = None
    tuesday: Optional[List[BusinessHoursSlot]] = None
    wednesday: Optional[List[BusinessHoursSlot]] = None
    thursday: Optional[List[BusinessHoursSlot]] = None
    friday: Optional[List[BusinessHoursSlot]] = None
    saturday: Optional[List[BusinessHoursSlot]] = None
    sunday: Optional[List[BusinessHoursSlot]] = None


class LocationAddress(BaseModel):
    """Standardized address information"""
    street_address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., pattern=r'^[A-Z]{2}$')
    postal_code: str = Field(..., pattern=r'^\d{5}(-\d{4})?$')
    country: str = Field("US", pattern=r'^[A-Z]{2}$')


class LocationContact(BaseModel):
    """Contact information for a location"""
    phone: Optional[str] = None
    website: Optional[str] = Field(None, pattern=r'^https?://')
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if v is None:
            return v
        
        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', v)
        
        # Convert to E.164 format
        if len(cleaned) == 10:
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            return f"+{cleaned}"
        elif len(cleaned) == 12 and cleaned.startswith('+'):
            return v
        else:
            raise ValueError(f"Invalid phone number format: {v}")


class LocationSchema(BaseModel):
    """Complete location schema for validation"""
    model_config = ConfigDict(extra='forbid')
    
    # Required fields
    business_name: str = Field(..., min_length=1, max_length=100)
    
    # Address information
    address: LocationAddress
    
    # Contact information
    contact: Optional[LocationContact] = None
    
    # Optional fields
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    hours: Optional[BusinessHours] = None
    categories: Optional[List[str]] = Field(None, max_length=10)
    attributes: Optional[Dict[str, Any]] = None
    
    # Metadata
    external_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=1000)
    
    # Status fields (for internal use)
    status: LocationStatus = LocationStatus.PENDING
    verification_status: VerificationStatus = VerificationStatus.NOT_STARTED
    apple_place_id: Optional[str] = None


class AppleLocationSchema(BaseModel):
    """Apple Business Connect specific location schema"""
    model_config = ConfigDict(extra='forbid')
    
    # Required fields for Apple
    business_name: str = Field(..., min_length=1, max_length=100)
    street_address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field("US", pattern=r'^[A-Z]{2}$')
    
    # Optional but recommended
    state: Optional[str] = Field(None, pattern=r'^[A-Z]{2}$')
    postal_code: Optional[str] = Field(None, pattern=r'^\d{5}(-\d{4})?$')
    phone: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    website: Optional[str] = Field(None, pattern=r'^https?://')
    hours: Optional[BusinessHours] = None
    categories: Optional[List[str]] = Field(None, max_length=5)
    attributes: Optional[Dict[str, Any]] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if v is None:
            return v
        
        # Convert to E.164 format
        cleaned = re.sub(r'\D', '', v)
        if len(cleaned) == 10:
            return f"+1{cleaned}"
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            return f"+{cleaned}"
        elif len(cleaned) == 12 and cleaned.startswith('+'):
            return v
        else:
            raise ValueError(f"Invalid phone number format: {v}")
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        if v is None:
            return v
        
        # Standardize ZIP code
        digits = re.sub(r'\D', '', v)
        if len(digits) == 5:
            return digits
        elif len(digits) == 9:
            return f"{digits[:5]}-{digits[5:]}"
        else:
            raise ValueError(f"Invalid postal code: {v}")


class YextLocationSchema(BaseModel):
    """Yext specific location schema"""
    model_config = ConfigDict(extra='allow')
    
    # Yext specific fields
    name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., pattern=r'^[A-Z]{2}$')
    zip: str = Field(..., pattern=r'^\d{5}(-\d{4})?$')
    country: str = Field("US", pattern=r'^[A-Z]{2}$')
    
    phone: Optional[str] = None
    websiteUrl: Optional[str] = Field(None, pattern=r'^https?://')
    
    # Categories and attributes
    categoryIds: Optional[List[str]] = None
    customFields: Optional[Dict[str, Any]] = None


class BulkUploadRequest(BaseModel):
    """Schema for bulk upload requests"""
    locations: List[LocationSchema]
    aggregator: str = Field(..., pattern=r'^(apple|yext|uberall|rio_seo)$')
    batch_size: int = Field(100, ge=1, le=1000)
    validate_only: bool = False
    dry_run: bool = False


class BulkUploadResponse(BaseModel):
    """Schema for bulk upload responses"""
    batch_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    validation_errors: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information"""
    field: str
    error_type: str
    message: str
    value: Any
    location_id: Optional[str] = None