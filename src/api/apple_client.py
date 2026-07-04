import jwt
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
from pathlib import Path

from .base_client import BaseAPIClient, APIResponse
from ..config.settings import Settings
from ..config.logging_config import get_logger


class AppleBusinessConnectClient(BaseAPIClient):
    """Apple Business Connect API client"""
    
    def __init__(self, settings: Settings):
        super().__init__(settings, "AppleBusinessConnect")
        self.settings = settings
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with JWT token"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        token = self._get_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        return headers
    
    def get_base_url(self) -> str:
        """Get Apple Business Connect API base URL"""
        return "https://businessconnect.apple.com/api/v1"
    
    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Apple API authentication"""
        try:
            # Read the private key
            private_key_path = Path(self.settings.apple.private_key_path)
            if not private_key_path.exists():
                raise FileNotFoundError(f"Private key file not found: {private_key_path}")
            
            with open(private_key_path, 'r') as key_file:
                private_key = key_file.read()
            
            # Create JWT payload
            now = int(time.time())
            payload = {
                'iss': self.settings.apple.team_id,
                'iat': now,
                'exp': now + 1800,  # 30 minutes
                'aud': 'https://apple.com/businessconnect'
            }
            
            # Generate JWT token
            token = jwt.encode(
                payload,
                private_key,
                algorithm='ES256',
                headers={
                    'kid': self.settings.apple.key_id
                }
            )
            
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to generate JWT token: {str(e)}")
            raise
    
    def _get_access_token(self) -> str:
        """Get or refresh access token"""
        # Check if we have a valid token
        if (self._access_token and 
            self._token_expires_at and 
            self._token_expires_at > datetime.now() + timedelta(minutes=5)):
            return self._access_token
        
        # Generate new token
        try:
            jwt_token = self._generate_jwt_token()
            
            # Exchange JWT for access token
            response = self.session.post(
                "https://apple.com/businessconnect/oauth/token",
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.settings.apple.client_id,
                    'client_secret': jwt_token
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data['access_token']
                self._token_expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
                
                self.logger.info("Successfully obtained Apple Business Connect access token")
                return self._access_token
            else:
                raise Exception(f"Failed to obtain access token: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to get access token: {str(e)}")
            raise
    
    def create_location(self, location_data: Dict[str, Any]) -> APIResponse:
        """Create a new location"""
        return self.post("/locations", json=location_data)
    
    def create_locations_bulk(self, locations: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple locations in bulk"""
        return self.post("/locations/bulk", json={"locations": locations})
    
    def get_location(self, location_id: str) -> APIResponse:
        """Get location details"""
        return self.get(f"/locations/{location_id}")
    
    def update_location(self, location_id: str, location_data: Dict[str, Any]) -> APIResponse:
        """Update location details"""
        return self.put(f"/locations/{location_id}", json=location_data)
    
    def delete_location(self, location_id: str) -> APIResponse:
        """Delete a location"""
        return self.delete(f"/locations/{location_id}")
    
    def get_locations(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """Get list of locations"""
        params = {
            "limit": limit,
            "offset": offset
        }
        return self.get("/locations", params=params)
    
    def trigger_verification(self, location_id: str) -> APIResponse:
        """Trigger verification for a location"""
        return self.post(f"/locations/{location_id}/verify")
    
    def get_verification_status(self, location_id: str) -> APIResponse:
        """Get verification status for a location"""
        return self.get(f"/locations/{location_id}/verification-status")
    
    def upload_media(self, media_data: Dict[str, Any]) -> APIResponse:
        """Upload media (images, logos, etc.)"""
        return self.post("/media", json=media_data)
    
    def delete_media(self, media_id: str) -> APIResponse:
        """Delete media"""
        return self.delete(f"/media/{media_id}")
    
    def get_analytics(self, location_id: str, start_date: str, end_date: str) -> APIResponse:
        """Get analytics data for a location"""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return self.get(f"/locations/{location_id}/analytics", params=params)
    
    def search_locations(self, query: str, limit: int = 50) -> APIResponse:
        """Search for locations"""
        params = {
            "q": query,
            "limit": limit
        }
        return self.get("/locations/search", params=params)
    
    def get_categories(self) -> APIResponse:
        """Get available business categories"""
        return self.get("/categories")
    
    def get_attributes(self, category_id: str) -> APIResponse:
        """Get available attributes for a category"""
        return self.get(f"/categories/{category_id}/attributes")
    
    def health_check(self) -> bool:
        """Check if Apple Business Connect API is accessible"""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_account_info(self) -> APIResponse:
        """Get account information"""
        return self.get("/account")
    
    def get_quota_info(self) -> APIResponse:
        """Get API quota and usage information"""
        return self.get("/quota")
    
    def validate_location_data(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location data against Apple's requirements"""
        required_fields = ['business_name', 'street_address', 'city', 'country']
        missing_fields = [field for field in required_fields if field not in location_data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate phone number format
        if 'phone' in location_data:
            phone = location_data['phone']
            if not self._is_valid_phone(phone):
                raise ValueError(f"Invalid phone number format: {phone}")
        
        # Validate postal code format
        if 'postal_code' in location_data:
            postal_code = location_data['postal_code']
            if not self._is_valid_postal_code(postal_code, location_data.get('country', 'US')):
                raise ValueError(f"Invalid postal code format: {postal_code}")
        
        # Validate business hours format
        if 'hours' in location_data:
            self._validate_business_hours(location_data['hours'])
        
        return location_data
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Simple validation - should be more comprehensive in production
        phone_pattern = r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$'
        return bool(re.match(phone_pattern, phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')))
    
    def _is_valid_postal_code(self, postal_code: str, country: str = 'US') -> bool:
        """Validate postal code format"""
        import re
        if country == 'US':
            return bool(re.match(r'^\d{5}(-\d{4})?$', postal_code))
        # Add validation for other countries as needed
        return True
    
    def _validate_business_hours(self, hours: Dict[str, Any]) -> None:
        """Validate business hours format"""
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day, slots in hours.items():
            if day not in valid_days:
                raise ValueError(f"Invalid day: {day}")
            
            if not isinstance(slots, list):
                raise ValueError(f"Business hours for {day} must be a list")
            
            for slot in slots:
                if not isinstance(slot, dict):
                    raise ValueError(f"Time slot must be a dictionary")
                
                if 'opens' not in slot or 'closes' not in slot:
                    raise ValueError(f"Time slot must contain 'opens' and 'closes' fields")
                
                opens = slot['opens']
                closes = slot['closes']
                
                if not self._is_valid_time_format(opens) or not self._is_valid_time_format(closes):
                    raise ValueError(f"Invalid time format in {day}: {opens}-{closes}")
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        import re
        return bool(re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str))