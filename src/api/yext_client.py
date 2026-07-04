from typing import Optional, Dict, Any, List
import json

from .base_client import BaseAPIClient, APIResponse
from ..config.settings import Settings
from ..config.logging_config import get_logger


class YextClient(BaseAPIClient):
    """Yext API client"""
    
    def __init__(self, settings: Settings):
        super().__init__(settings, "Yext")
        self.settings = settings
        self.account_id = settings.yext.account_id
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with API key"""
        return {
            "Authorization": f"Bearer {self.settings.yext.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_base_url(self) -> str:
        """Get Yext API base URL"""
        return f"https://api.yext.com/v2/accounts/{self.account_id}"
    
    def create_location(self, location_data: Dict[str, Any]) -> APIResponse:
        """Create a new location in Yext"""
        return self.post("/entities", json=location_data)
    
    def create_locations_bulk(self, locations: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple locations in bulk"""
        return self.post("/bulk/entities", json={"entities": locations})
    
    def get_location(self, location_id: str) -> APIResponse:
        """Get location details from Yext"""
        return self.get(f"/entities/{location_id}")
    
    def update_location(self, location_id: str, location_data: Dict[str, Any]) -> APIResponse:
        """Update location in Yext"""
        return self.put(f"/entities/{location_id}", json=location_data)
    
    def delete_location(self, location_id: str) -> APIResponse:
        """Delete location from Yext"""
        return self.delete(f"/entities/{location_id}")
    
    def get_locations(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """Get list of locations from Yext"""
        params = {
            "limit": limit,
            "offset": offset,
            "entityTypes": "location"
        }
        return self.get("/entities", params=params)
    
    def search_locations(self, query: str, limit: int = 50) -> APIResponse:
        """Search for locations in Yext"""
        params = {
            "q": query,
            "limit": limit,
            "entityTypes": "location"
        }
        return self.get("/entities", params=params)
    
    def get_folders(self) -> APIResponse:
        """Get location folders"""
        return self.get("/folders")
    
    def create_folder(self, folder_data: Dict[str, Any]) -> APIResponse:
        """Create a new folder"""
        return self.post("/folders", json=folder_data)
    
    def get_entity_types(self) -> APIResponse:
        """Get available entity types"""
        return self.get("/entitytypes")
    
    def get_custom_fields(self) -> APIResponse:
        """Get custom fields"""
        return self.get("/customfields")
    
    def health_check(self) -> bool:
        """Check if Yext API is accessible"""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Yext health check failed: {str(e)}")
            return False


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


class RioSeoClient(BaseAPIClient):
    """Rio SEO API client"""
    
    def __init__(self, settings: Settings):
        super().__init__(settings, "RioSeo")
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with API key"""
        return {
            "Authorization": f"Bearer {self.settings.rio_seo.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_base_url(self) -> str:
        """Get Rio SEO API base URL"""
        return "https://api.rioseo.com/v1"
    
    def create_location(self, location_data: Dict[str, Any]) -> APIResponse:
        """Create a new location in Rio SEO"""
        return self.post("/locations", json=location_data)
    
    def create_locations_bulk(self, locations: List[Dict[str, Any]]) -> APIResponse:
        """Create multiple locations in bulk"""
        return self.post("/locations/bulk", json={"locations": locations})
    
    def get_location(self, location_id: str) -> APIResponse:
        """Get location details from Rio SEO"""
        return self.get(f"/locations/{location_id}")
    
    def update_location(self, location_id: str, location_data: Dict[str, Any]) -> APIResponse:
        """Update location in Rio SEO"""
        return self.put(f"/locations/{location_id}", json=location_data)
    
    def delete_location(self, location_id: str) -> APIResponse:
        """Delete location from Rio SEO"""
        return self.delete(f"/locations/{location_id}")
    
    def get_locations(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """Get list of locations from Rio SEO"""
        params = {
            "limit": limit,
            "offset": offset
        }
        return self.get("/locations", params=params)
    
    def get_location_performance(self, location_id: str) -> APIResponse:
        """Get performance metrics for a location"""
        return self.get(f"/locations/{location_id}/performance")
    
    def get_location_rankings(self, location_id: str, keywords: List[str]) -> APIResponse:
        """Get search rankings for a location"""
        data = {"keywords": keywords}
        return self.post(f"/locations/{location_id}/rankings", json=data)
    
    def get_templates(self) -> APIResponse:
        """Get available templates"""
        return self.get("/templates")
    
    def health_check(self) -> bool:
        """Check if Rio SEO API is accessible"""
        try:
            response = self.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Rio SEO health check failed: {str(e)}")
            return False