from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
import pandas as pd

from .schema import LocationSchema, AppleLocationSchema, ValidationErrorDetail
from ..config.logging_config import get_logger


class DataValidator:
    """Validate location data against schemas"""
    
    def __init__(self):
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def validate_locations(self, locations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[ValidationErrorDetail]]:
        """Validate a list of location data"""
        valid_locations = []
        validation_errors = []
        
        for i, location_data in enumerate(locations):
            try:
                # Validate against LocationSchema
                validated_location = LocationSchema(**location_data)
                valid_locations.append(validated_location.model_dump())
                
            except ValidationError as e:
                # Capture validation errors
                for error in e.errors():
                    error_detail = ValidationErrorDetail(
                        field='.'.join(str(loc) for loc in error['loc']),
                        error_type=error['type'],
                        message=error['msg'],
                        value=error.get('input'),
                        location_id=location_data.get('external_id') or location_data.get('id') or str(i)
                    )
                    validation_errors.append(error_detail)
                
                self.logger.warning(f"Location {i} failed validation: {error}")
            
            except Exception as e:
                # Handle other validation errors
                error_detail = ValidationErrorDetail(
                    field='general',
                    error_type='validation_error',
                    message=str(e),
                    value=location_data,
                    location_id=location_data.get('external_id') or location_data.get('id') or str(i)
                )
                validation_errors.append(error_detail)
                self.logger.warning(f"Location {i} validation failed: {str(e)}")
        
        self.logger.info(f"Validation complete: {len(valid_locations)} valid, {len(validation_errors)} errors")
        return valid_locations, validation_errors
    
    def validate_for_apple(self, locations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[ValidationErrorDetail]]:
        """Validate locations specifically for Apple Business Connect"""
        valid_locations = []
        validation_errors = []
        
        for i, location_data in enumerate(locations):
            try:
                # Transform to Apple format first
                apple_data = self._transform_to_apple_format(location_data)
                
                # Validate against Apple schema
                validated_location = AppleLocationSchema(**apple_data)
                valid_locations.append(validated_location.model_dump())
                
            except ValidationError as e:
                for error in e.errors():
                    error_detail = ValidationErrorDetail(
                        field='.'.join(str(loc) for loc in error['loc']),
                        error_type=error['type'],
                        message=error['msg'],
                        value=error.get('input'),
                        location_id=location_data.get('external_id') or str(i)
                    )
                    validation_errors.append(error_detail)
                
                self.logger.warning(f"Apple validation failed for location {i}: {error}")
            
            except Exception as e:
                error_detail = ValidationErrorDetail(
                    field='general',
                    error_type='apple_validation_error',
                    message=str(e),
                    value=location_data,
                    location_id=location_data.get('external_id') or str(i)
                )
                validation_errors.append(error_detail)
                self.logger.warning(f"Apple validation failed for location {i}: {str(e)}")
        
        return valid_locations, validation_errors
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[ValidationErrorDetail]]:
        """Validate pandas DataFrame"""
        validation_errors = []
        valid_indices = []
        
        for index, row in df.iterrows():
            try:
                # Convert row to dict
                row_dict = row.to_dict()
                
                # Validate against LocationSchema
                LocationSchema(**row_dict)
                valid_indices.append(index)
                
            except ValidationError as e:
                for error in e.errors():
                    error_detail = ValidationErrorDetail(
                        field='.'.join(str(loc) for loc in error['loc']),
                        error_type=error['type'],
                        message=error['msg'],
                        value=error.get('input'),
                        location_id=str(index)
                    )
                    validation_errors.append(error_detail)
                
                self.logger.warning(f"Row {index} failed validation: {error}")
            
            except Exception as e:
                error_detail = ValidationErrorDetail(
                    field='general',
                    error_type='validation_error',
                    message=str(e),
                    value=row.to_dict(),
                    location_id=str(index)
                )
                validation_errors.append(error_detail)
                self.logger.warning(f"Row {index} validation failed: {str(e)}")
        
        # Create DataFrame with only valid rows
        valid_df = df.loc[valid_indices] if valid_indices else pd.DataFrame()
        
        self.logger.info(f"DataFrame validation: {len(valid_df)} valid rows, {len(validation_errors)} errors")
        return valid_df, validation_errors
    
    def _transform_to_apple_format(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform location data to Apple Business Connect format"""
        apple_data = {
            'business_name': location_data.get('business_name') or location_data.get('name', ''),
            'street_address': location_data.get('street_address') or location_data.get('address', ''),
            'city': location_data.get('city', ''),
            'country': location_data.get('country', 'US')
        }
        
        # Add optional fields
        if location_data.get('state'):
            apple_data['state'] = location_data['state']
        
        if location_data.get('postal_code') or location_data.get('zip'):
            apple_data['postal_code'] = location_data.get('postal_code') or location_data.get('zip')
        
        if location_data.get('phone'):
            apple_data['phone'] = location_data['phone']
        
        if location_data.get('website'):
            apple_data['website'] = location_data['website']
        
        if location_data.get('hours'):
            apple_data['hours'] = location_data['hours']
        
        if location_data.get('categories'):
            apple_data['categories'] = location_data['categories'][:5]  # Apple limit
        
        return apple_data
    
    def get_validation_summary(self, validation_errors: List[ValidationErrorDetail]) -> Dict[str, Any]:
        """Get summary statistics of validation errors"""
        if not validation_errors:
            return {
                'total_errors': 0,
                'error_types': {},
                'fields_with_errors': {},
                'severity': 'none'
            }
        
        # Count error types
        error_types = {}
        fields_with_errors = {}
        
        for error in validation_errors:
            # Count error types
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count fields with errors
            field = error.field
            fields_with_errors[field] = fields_with_errors.get(field, 0) + 1
        
        # Determine severity
        total_errors = len(validation_errors)
        if total_errors == 0:
            severity = 'none'
        elif total_errors < 10:
            severity = 'low'
        elif total_errors < 50:
            severity = 'medium'
        else:
            severity = 'high'
        
        return {
            'total_errors': total_errors,
            'error_types': error_types,
            'fields_with_errors': fields_with_errors,
            'severity': severity,
            'unique_locations_affected': len(set(error.location_id for error in validation_errors))
        }
    
    def generate_error_report(self, validation_errors: List[ValidationErrorDetail]) -> pd.DataFrame:
        """Generate detailed error report as DataFrame"""
        if not validation_errors:
            return pd.DataFrame()
        
        error_data = []
        for error in validation_errors:
            error_data.append({
                'location_id': error.location_id,
                'field': error.field,
                'error_type': error.error_type,
                'message': error.message,
                'value': str(error.value)[:100] if error.value else None  # Truncate long values
            })
        
        return pd.DataFrame(error_data)
    
    def validate_field_completeness(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check completeness of required fields across all locations"""
        required_fields = ['business_name', 'street_address', 'city', 'state', 'postal_code']
        optional_fields = ['phone', 'website', 'latitude', 'longitude', 'hours']
        
        field_completeness = {}
        total_locations = len(locations)
        
        # Count missing values for each field
        for field in required_fields + optional_fields:
            missing_count = sum(1 for location in locations if not location.get(field))
            field_completeness[field] = {
                'present': total_locations - missing_count,
                'missing': missing_count,
                'completeness_percentage': round((total_locations - missing_count) / total_locations * 100, 2) if total_locations > 0 else 0
            }
        
        # Calculate overall data quality score
        required_completeness_scores = [
            field_completeness[field]['completeness_percentage'] 
            for field in required_fields
        ]
        
        overall_quality = round(sum(required_completeness_scores) / len(required_completeness_scores), 2)
        
        return {
            'total_locations': total_locations,
            'field_completeness': field_completeness,
            'overall_quality_score': overall_quality,
            'quality_tier': self._get_quality_tier(overall_quality)
        }
    
    def _get_quality_tier(self, quality_score: float) -> str:
        """Determine quality tier based on completeness score"""
        if quality_score >= 95:
            return 'excellent'
        elif quality_score >= 80:
            return 'good'
        elif quality_score >= 60:
            return 'fair'
        else:
            return 'poor'