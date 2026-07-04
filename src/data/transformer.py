from typing import List, Dict, Any, Optional
from enum import Enum

from .schema import LocationSchema, AppleLocationSchema, YextLocationSchema
from ..config.logging_config import get_logger


class AggregatorType(str, Enum):
    APPLE = "apple"
    YEXT = "yext"
    UBERALL = "uberall"
    RIO_SEO = "rio_seo"


class DataTransformer:
    """Transform location data between different formats"""
    
    def __init__(self):
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def transform_to_aggregator_format(
        self,
        location_data: Dict[str, Any],
        aggregator: AggregatorType
    ) -> Dict[str, Any]:
        """Transform location data to specific aggregator format"""
        
        if aggregator == AggregatorType.APPLE:
            return self._to_apple_format(location_data)
        elif aggregator == AggregatorType.YEXT:
            return self._to_yext_format(location_data)
        elif aggregator == AggregatorType.UBERALL:
            return self._to_uberall_format(location_data)
        elif aggregator == AggregatorType.RIO_SEO:
            return self._to_rio_seo_format(location_data)
        else:
            raise ValueError(f"Unsupported aggregator: {aggregator}")
    
    def transform_batch_to_aggregator_format(
        self,
        locations: List[Dict[str, Any]],
        aggregator: AggregatorType
    ) -> List[Dict[str, Any]]:
        """Transform batch of locations to aggregator format"""
        transformed_locations = []
        failed_transforms = []
        
        for i, location in enumerate(locations):
            try:
                transformed = self.transform_to_aggregator_format(location, aggregator)
                transformed_locations.append(transformed)
            except Exception as e:
                self.logger.warning(f"Failed to transform location {i} to {aggregator}: {str(e)}")
                failed_transforms.append({
                    'index': i,
                    'location_id': location.get('external_id') or location.get('id') or str(i),
                    'error': str(e)
                })
        
        if failed_transforms:
            self.logger.warning(f"Failed to transform {len(failed_transforms)} locations")
        
        return transformed_locations
    
    def _to_apple_format(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Apple Business Connect format"""
        apple_data = {
            'business_name': location_data.get('business_name') or location_data.get('name', ''),
            'street_address': location_data.get('street_address') or location_data.get('address', ''),
            'city': location_data.get('city', ''),
            'country': location_data.get('country', 'US')
        }
        
        # Add required address fields
        if location_data.get('state'):
            apple_data['state'] = location_data['state']
        else:
            raise ValueError("State is required for Apple Business Connect")
        
        if location_data.get('postal_code') or location_data.get('zip'):
            apple_data['postal_code'] = location_data.get('postal_code') or location_data.get('zip')
        else:
            raise ValueError("Postal code is required for Apple Business Connect")
        
        # Add optional fields
        if location_data.get('phone'):
            apple_data['phone'] = self._format_phone_for_apple(location_data['phone'])
        
        if location_data.get('website'):
            apple_data['website'] = self._validate_url(location_data['website'])
        
        if location_data.get('latitude') and location_data.get('longitude'):
            apple_data['latitude'] = float(location_data['latitude'])
            apple_data['longitude'] = float(location_data['longitude'])
        
        # Transform business hours
        if location_data.get('hours'):
            apple_data['hours'] = self._transform_hours_for_apple(location_data['hours'])
        
        # Transform categories (max 5)
        if location_data.get('categories'):
            apple_data['categories'] = location_data['categories'][:5]
        
        # Transform attributes
        if location_data.get('attributes'):
            apple_data['attributes'] = self._transform_attributes_for_apple(location_data['attributes'])
        
        return apple_data
    
    def _to_yext_format(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Yext format"""
        yext_data = {
            'name': location_data.get('business_name') or location_data.get('name', ''),
            'address': location_data.get('street_address') or location_data.get('address', ''),
            'city': location_data.get('city', ''),
            'state': location_data.get('state', ''),
            'zip': location_data.get('postal_code') or location_data.get('zip', ''),
            'country': location_data.get('country', 'US')
        }
        
        # Add optional fields
        if location_data.get('phone'):
            yext_data['phone'] = self._format_phone_for_yext(location_data['phone'])
        
        if location_data.get('website'):
            yext_data['websiteUrl'] = self._validate_url(location_data['website'])
        
        # Add custom fields
        yext_data['customFields'] = {
            'source_system': 'bulk_import',
            'import_timestamp': self._get_current_timestamp()
        }
        
        # Add categories if available
        if location_data.get('categories'):
            yext_data['categoryIds'] = location_data['categories']
        
        # Add attributes as custom fields
        if location_data.get('attributes'):
            yext_data['customFields'].update(location_data['attributes'])
        
        return yext_data
    
    def _to_uberall_format(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Uberall format"""
        uberall_data = {
            'companyName': location_data.get('business_name') or location_data.get('name', ''),
            'street': location_data.get('street_address') or location_data.get('address', ''),
            'city': location_data.get('city', ''),
            'state': location_data.get('state', ''),
            'zip': location_data.get('postal_code') or location_data.get('zip', ''),
            'country': location_data.get('country', 'US')
        }
        
        # Add optional fields
        if location_data.get('phone'):
            uberall_data['phone'] = self._format_phone_for_uberall(location_data['phone'])
        
        if location_data.get('website'):
            uberall_data['website'] = self._validate_url(location_data['website'])
        
        # Add geolocation if available
        if location_data.get('latitude') and location_data.get('longitude'):
            uberall_data['geoCoords'] = {
                'latitude': float(location_data['latitude']),
                'longitude': float(location_data['longitude'])
            }
        
        # Add business hours if available
        if location_data.get('hours'):
            uberall_data['businessHours'] = self._transform_hours_for_uberall(location_data['hours'])
        
        # Add custom attributes
        if location_data.get('attributes'):
            uberall_data['additionalAttributes'] = location_data['attributes']
        
        return uberall_data
    
    def _to_rio_seo_format(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to Rio SEO format"""
        rio_seo_data = {
            'location_name': location_data.get('business_name') or location_data.get('name', ''),
            'street_address': location_data.get('street_address') or location_data.get('address', ''),
            'locality': location_data.get('city', ''),
            'region': location_data.get('state', ''),
            'postal_code': location_data.get('postal_code') or location_data.get('zip', ''),
            'country': location_data.get('country', 'US')
        }
        
        # Add contact information
        if location_data.get('phone'):
            rio_seo_data['phone'] = self._format_phone_for_rio_seo(location_data['phone'])
        
        if location_data.get('website'):
            rio_seo_data['website_url'] = self._validate_url(location_data['website'])
        
        # Add location profile data
        if location_data.get('hours'):
            rio_seo_data['opening_hours'] = self._transform_hours_for_rio_seo(location_data['hours'])
        
        # Add categories
        if location_data.get('categories'):
            rio_seo_data['categories'] = location_data['categories']
        
        # Add custom attributes
        if location_data.get('attributes'):
            rio_seo_data['custom_attributes'] = location_data['attributes']
        
        return rio_seo_data
    
    def _format_phone_for_apple(self, phone: str) -> str:
        """Format phone number for Apple (E.164)"""
        import re
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Format to E.164
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif len(digits) == 12 and digits.startswith('+'):
            return digits
        else:
            raise ValueError(f"Invalid phone number format for Apple: {phone}")
    
    def _format_phone_for_yext(self, phone: str) -> str:
        """Format phone number for Yext"""
        # Yext typically accepts standard phone format
        return phone
    
    def _format_phone_for_uberall(self, phone: str) -> str:
        """Format phone number for Uberall"""
        # Uberall typically accepts standard phone format
        return phone
    
    def _format_phone_for_rio_seo(self, phone: str) -> str:
        """Format phone number for Rio SEO"""
        # Rio SEO typically accepts standard phone format
        return phone
    
    def _validate_url(self, url: str) -> str:
        """Validate and format URL"""
        if not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url
    
    def _transform_hours_for_apple(self, hours: Dict[str, Any]) -> Dict[str, Any]:
        """Transform business hours for Apple format"""
        # Apple expects specific format for business hours
        apple_hours = {}
        
        day_mapping = {
            'monday': 'monday',
            'tuesday': 'tuesday', 
            'wednesday': 'wednesday',
            'thursday': 'thursday',
            'friday': 'friday',
            'saturday': 'saturday',
            'sunday': 'sunday'
        }
        
        for day, slots in hours.items():
            if day in day_mapping and slots:
                apple_hours[day_mapping[day]] = [
                    {
                        'opens': slot.get('opens', '09:00'),
                        'closes': slot.get('closes', '17:00')
                    }
                    for slot in slots if isinstance(slot, dict)
                ]
        
        return apple_hours
    
    def _transform_hours_for_uberall(self, hours: Dict[str, Any]) -> Dict[str, Any]:
        """Transform business hours for Uberall format"""
        return hours  # Uberall format is similar to our standard format
    
    def _transform_hours_for_rio_seo(self, hours: Dict[str, Any]) -> Dict[str, Any]:
        """Transform business hours for Rio SEO format"""
        return hours  # Rio SEO format is similar to our standard format
    
    def _transform_attributes_for_apple(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Transform attributes for Apple format"""
        # Filter and transform attributes for Apple
        apple_attributes = {}
        
        # Apple has specific attribute names and formats
        attribute_mapping = {
            'description': 'description',
            'email': 'email',
            'primary_category': 'primaryCategory'
        }
        
        for key, value in attributes.items():
            if key in attribute_mapping:
                apple_attributes[attribute_mapping[key]] = value
            elif key.startswith('custom_'):
                # Custom attributes go under specific key
                if 'customAttributes' not in apple_attributes:
                    apple_attributes['customAttributes'] = {}
                apple_attributes['customAttributes'][key.replace('custom_', '')] = value
        
        return apple_attributes
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for tracking"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def get_transformation_report(
        self,
        original_count: int,
        transformed_count: int,
        failed_count: int,
        aggregator: AggregatorType
    ) -> Dict[str, Any]:
        """Generate transformation report"""
        success_rate = (transformed_count / original_count * 100) if original_count > 0 else 0
        
        return {
            'aggregator': aggregator.value,
            'original_count': original_count,
            'transformed_count': transformed_count,
            'failed_count': failed_count,
            'success_rate': round(success_rate, 2),
            'transformation_efficiency': 'high' if success_rate >= 95 else 'medium' if success_rate >= 80 else 'low'
        }