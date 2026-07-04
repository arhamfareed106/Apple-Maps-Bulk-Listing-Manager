#!/usr/bin/env python3
"""
Example script demonstrating Apple Maps Bulk Listing Manager usage
"""

import asyncio
import json
from pathlib import Path
import pandas as pd

from src.config.settings import Settings
from src.config.logging_config import setup_logging, get_logger
from src.engine.bulk_uploader import BulkUploader
from src.data.reader import DataReader
from src.data.processor import DataProcessor
from src.data.validator import DataValidator
from src.data.transformer import DataTransformer, AggregatorType


async def create_sample_data():
    """Create sample location data for testing"""
    sample_data = [
        {
            "business_name": "Sample Store 1",
            "street_address": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US",
            "phone": "+12125550123",
            "website": "https://sample1.com",
            "hours": {
                "monday": [{"opens": "09:00", "closes": "17:00"}],
                "tuesday": [{"opens": "09:00", "closes": "17:00"}],
                "wednesday": [{"opens": "09:00", "closes": "17:00"}],
                "thursday": [{"opens": "09:00", "closes": "17:00"}],
                "friday": [{"opens": "09:00", "closes": "17:00"}]
            }
        },
        {
            "business_name": "Sample Store 2",
            "street_address": "456 Oak Avenue",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90210",
            "country": "US",
            "phone": "+13105550456",
            "website": "https://sample2.com"
        }
    ]
    
    # Create sample files
    data_dir = Path("data/input")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_file = data_dir / "sample_locations.json"
    with open(json_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    # Save as CSV
    csv_file = data_dir / "sample_locations.csv"
    df = pd.DataFrame(sample_data)
    df.to_csv(csv_file, index=False)
    
    print(f"Created sample data files:")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    
    return str(csv_file)


async def example_file_preview():
    """Example of file preview functionality"""
    print("=== File Preview Example ===")
    
    # Create sample data
    csv_file = await create_sample_data()
    
    # Preview the file
    reader = DataReader()
    preview_data = reader.preview_file(csv_file, rows=3)
    
    print(f"File: {preview_data['name']}")
    print(f"Format: {preview_data['format']}")
    print(f"Rows: {preview_data['rows']}")
    print(f"Size: {preview_data['size_mb']} MB")
    print(f"Columns: {', '.join(preview_data['columns'])}")


async def example_data_processing():
    """Example of data processing workflow"""
    print("\n=== Data Processing Example ===")
    
    # Create sample data
    csv_file = await create_sample_data()
    
    # Initialize components
    settings = Settings()
    reader = DataReader()
    processor = DataProcessor()
    validator = DataValidator()
    
    # Read data
    raw_data = reader.read_file(csv_file)
    print(f"Read {len(raw_data)} records")
    
    # Process data
    if isinstance(raw_data, pd.DataFrame):
        processed_data = processor.process_dataframe(raw_data, source_type='file')
    else:
        processed_data = raw_data
    
    print(f"Processed {len(processed_data)} records")
    
    # Validate data
    valid_data, validation_errors = validator.validate_locations(processed_data)
    print(f"Valid records: {len(valid_data)}")
    print(f"Validation errors: {len(validation_errors)}")
    
    if validation_errors:
        print("Validation errors:")
        for error in validation_errors[:3]:  # Show first 3 errors
            print(f"  - {error.field}: {error.message}")


async def example_data_transformation():
    """Example of data transformation for different aggregators"""
    print("\n=== Data Transformation Example ===")
    
    # Create sample data
    json_file = await create_sample_data()
    
    # Read data
    with open(json_file, 'r') as f:
        locations_data = json.load(f)
    
    # Transform for different aggregators
    transformer = DataTransformer()
    
    for aggregator in [AggregatorType.APPLE, AggregatorType.YEXT, AggregatorType.UBERALL]:
        print(f"\n--- {aggregator.value.upper()} Format ---")
        
        try:
            transformed_data = [
                transformer.transform_to_aggregator_format(loc, aggregator)
                for loc in locations_data
            ]
            
            print(f"Transformed {len(transformed_data)} locations")
            if transformed_data:
                print("Sample transformed data:")
                print(json.dumps(transformed_data[0], indent=2, default=str)[:200] + "...")
                
        except Exception as e:
            print(f"Transformation failed: {e}")


async def example_upload_simulation():
    """Example of upload simulation (without actual API calls)"""
    print("\n=== Upload Simulation Example ===")
    
    try:
        # Create sample data
        csv_file = await create_sample_data()
        
        # Initialize settings
        settings = Settings()
        setup_logging(settings)
        
        # Initialize uploader in validate-only mode
        print("Simulating upload to Apple Business Connect (validate-only mode)...")
        uploader = BulkUploader(settings)
        
        # Run upload with validation only
        result = await uploader.upload_from_file(
            file_path=csv_file,
            aggregator="apple",
            validate_only=True
        )
        
        print(f"Simulation results:")
        print(f"  Total records: {result.total_records}")
        print(f"  Valid records: {result.valid_records}")
        print(f"  Invalid records: {result.invalid_records}")
        print(f"  Status: {result.status}")
        
        uploader.close()
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        # Continue with other examples even if upload fails


def main():
    """Main example function"""
    print("Apple Maps Bulk Listing Manager - Examples")
    print("=" * 50)
    
    # Run all examples
    try:
        # Run file preview example
        asyncio.run(example_file_preview())
        
        # Run data processing example
        asyncio.run(example_data_processing())
        
        # Run transformation example
        asyncio.run(example_data_transformation())
        
        # Run upload simulation example
        asyncio.run(example_upload_simulation())
        
        print("\n=== Usage Examples ===")
        print("Preview file contents:")
        print("  python -m src.main preview data/input/sample_locations.csv")
        print("")
        print("Upload file:")
        print("  python -m src.main upload data/input/sample_locations.csv --aggregator apple")
        print("")
        print("Validate data only:")
        print("  python -m src.main upload data/input/sample_locations.csv --validate-only")
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    main()