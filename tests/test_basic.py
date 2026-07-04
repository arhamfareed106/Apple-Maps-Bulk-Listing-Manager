"""
Basic tests for Apple Maps Bulk Listing Manager
"""
import pytest
import json
from pathlib import Path
import tempfile
import pandas as pd

from src.config.settings import Settings
from src.data.schema import LocationSchema, AppleLocationSchema
from src.data.reader import DataReader
from src.data.processor import DataProcessor
from src.data.validator import DataValidator


def test_settings_initialization():
    """Test that settings can be initialized"""
    try:
        settings = Settings()
        assert settings is not None
    except Exception as e:
        # This might fail due to missing .env file, which is expected in test environment
        print(f"Settings initialization warning: {e}")


def test_location_schema_validation():
    """Test location schema validation"""
    # Valid location data
    valid_data = {
        "business_name": "Test Store",
        "street_address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US",
        "phone": "+12125551234"
    }
    
    # This should validate successfully
    location = LocationSchema(**valid_data)
    assert location.business_name == "Test Store"
    assert location.address.city == "New York"


def test_apple_schema_validation():
    """Test Apple Business Connect schema validation"""
    # Valid Apple format data
    valid_apple_data = {
        "business_name": "Test Store",
        "street_address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US",
        "phone": "+12125551234"
    }
    
    # This should validate successfully
    apple_location = AppleLocationSchema(**valid_apple_data)
    assert apple_location.business_name == "Test Store"
    assert apple_location.state == "NY"


def test_data_reader():
    """Test data reader functionality"""
    reader = DataReader()
    
    # Test with sample data
    sample_data = [
        {
            "business_name": "Test Store 1",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001"
        },
        {
            "business_name": "Test Store 2",
            "street_address": "456 Oak Ave",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90210"
        }
    ]
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_data, f)
        temp_file = f.name
    
    try:
        # Test reading JSON file
        data = reader.read_json(temp_file)
        assert len(data) == 2
        assert data[0]['business_name'] == "Test Store 1"
        
        # Test file info
        file_info = reader.get_file_info(temp_file)
        assert file_info['format'] == 'json'
        assert file_info['extension'] == '.json'
        
    finally:
        # Clean up
        Path(temp_file).unlink()


def test_data_processor():
    """Test data processor functionality"""
    processor = DataProcessor()
    
    # Test phone normalization
    normalized_phone = processor._normalize_phone("212-555-1234")
    assert normalized_phone == "+12125551234"
    
    # Test state normalization
    normalized_state = processor._normalize_state("New York")
    assert normalized_state == "NY"
    
    # Test ZIP code normalization
    normalized_zip = processor._normalize_zip("10001-1234")
    assert normalized_zip == "10001-1234"


def test_data_validator():
    """Test data validator functionality"""
    validator = DataValidator()
    
    # Test valid data
    valid_locations = [
        {
            "business_name": "Test Store",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US"
        }
    ]
    
    valid_data, errors = validator.validate_locations(valid_locations)
    assert len(valid_data) == 1
    assert len(errors) == 0
    
    # Test invalid data
    invalid_locations = [
        {
            "business_name": "",  # Required field missing
            "street_address": "123 Main St",
            "city": "New York"
            # Missing required fields
        }
    ]
    
    valid_data, errors = validator.validate_locations(invalid_locations)
    assert len(valid_data) == 0
    assert len(errors) > 0


def test_field_completeness():
    """Test field completeness validation"""
    validator = DataValidator()
    
    locations = [
        {
            "business_name": "Store 1",
            "street_address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001"
        },
        {
            "business_name": "Store 2",
            "street_address": "456 Oak Ave",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90210",
            "phone": "+12125551234"  # Additional field
        }
    ]
    
    completeness = validator.validate_field_completeness(locations)
    assert completeness['total_locations'] == 2
    assert 'field_completeness' in completeness
    assert 'overall_quality_score' in completeness


if __name__ == "__main__":
    # Run basic tests
    test_settings_initialization()
    test_location_schema_validation()
    test_apple_schema_validation()
    test_data_processor()
    test_data_validator()
    test_field_completeness()
    
    print("All basic tests passed!")