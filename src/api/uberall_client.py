from typing import Optional, Dict, Any, List
import json

from .base_client import BaseAPIClient, APIResponse
from ..config.settings import Settings
from ..config.logging_config import get_logger


class UberallClient(BaseAPIClient):
    """Uberall API client"""
    
    def __init__(self, settings: Settings):
        super().__init__(settings, "Uberall")
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with API key"""
        return {
            "Authorization": f"Bearer {self.settings.uberall.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_base_url(self) -> str:
        """Get Uberall API base URL"""
        return "https://uberall.com/api"
    
    def create_location(self, location_data: Dict[str, Any]) -> APIResponse:
        """Create a new location in Uberall"""
        return self.post("/locations", json=location_data)
    
    def create_locations_bulk(self, locations: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple locations in bulk"""
        return self.post("/locations/bulk", json={"locations": locations})
    
    def get_location(self, location_id: str) -> APIResponse:
        """Get location details from Uberall"""
        return self.get(f"/locations/{location_id}")
    
    def update_location(self, location_id: str, location_data: Dict[str, Any]) -> APIResponse:
        """Update location in Uberall"""
        return self.put(f"/locations/{location_id}", json=location_data)
    
    def delete_location(self, location_id: str) -> APIResponse:
        """Delete location from Uberall"""
        return self.delete(f"/locations/{location_id}")
    
    def get_locations(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """Get list of locations from Uberall"""
        params = {
            "limit": limit,
            "offset": offset
        }
        return self.get("/locations", params=params)
    
    def get_location_listings(self, location_id: str) -> APIResponse:
        """Get listings for a specific location"""
        return self.get(f"/locations/{location_id}/listings")
    
    def update_listing(self, location_id: str, listing_id: str, listing_data: Dict[str, Any]) -> APIResponse:
        """Update a specific listing"""
        return self.put(f"/locations/{location_id}/listings/{listing_id}", json=listing_data)
    
    def get_categories(self) -> APIResponse:
        """Get available categories"""
        return self.get("/categories")
    
    def get_countries(self) -> APIResponse:
        """Get supported countries"""
        return self.get("/countries")
    
    def health_check(self) -> bool:
        """Check if Uberall API is accessible"""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Uberall health check failed: {str(e)}")
            return False