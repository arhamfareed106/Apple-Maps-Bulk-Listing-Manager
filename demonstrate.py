#!/usr/bin/env python3
"""
Simple demonstration script for Apple Maps Bulk Listing Manager
"""

import sys
import json
import os

# Add current directory to path
sys.path.insert(0, '.')

def demonstrate_functionality():
    """Demonstrate the core functionality of the system"""
    
    print("=" * 60)
    print("APPLE MAPS BULK LISTING MANAGER - DEMONSTRATION")
    print("=" * 60)
    
    # 1. Show sample data
    print("\n1. SAMPLE DATA FILE")
    print("-" * 30)
    
    sample_file = "data/input/sample_locations.json"
    if os.path.exists(sample_file):
        with open(sample_file, 'r') as f:
            sample_data = json.load(f)
        
        print(f"File: {sample_file}")
        print(f"Records: {len(sample_data)}")
        print("\nSample Record:")
        print(json.dumps(sample_data[0], indent=2))
    else:
        print("Sample data file not found!")
        return False
    
    # 2. Test data reader
    print("\n2. DATA READER FUNCTIONALITY")
    print("-" * 30)
    
    try:
        from src.data.reader import DataReader
        reader = DataReader()
        
        # Preview the file
        preview_data = reader.preview_file(sample_file)
        print("File Preview:")
        print(f"  Format: {preview_data['format']}")
        print(f"  Rows: {preview_data['rows']}")
        print(f"  Size: {preview_data['size_mb']} MB")
        print(f"  Columns: {', '.join(preview_data['columns'])}")
        
    except Exception as e:
        print(f"Error testing data reader: {e}")
        return False
    
    # 3. Test data validation
    print("\n3. DATA VALIDATION")
    print("-" * 30)
    
    try:
        from src.data.validator import DataValidator
        validator = DataValidator()
        
        # Validate the sample data
        valid_data, errors = validator.validate_locations(sample_data)
        print(f"Valid records: {len(valid_data)}")
        print(f"Invalid records: {len(errors)}")
        
        if errors:
            print("Validation errors:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error.field}: {error.message}")
        
        # Field completeness
        completeness = validator.validate_field_completeness(sample_data)
        print(f"Overall quality score: {completeness['overall_quality_score']}%")
        
    except Exception as e:
        print(f"Error testing data validation: {e}")
        return False
    
    # 4. Test data transformation
    print("\n4. DATA TRANSFORMATION")
    print("-" * 30)
    
    try:
        from src.data.transformer import DataTransformer, AggregatorType
        transformer = DataTransformer()
        
        # Transform to Apple format
        apple_data = transformer.transform_to_aggregator_format(
            sample_data[0], AggregatorType.APPLE
        )
        print("Apple Business Connect Format:")
        print(json.dumps(apple_data, indent=2))
        
    except Exception as e:
        print(f"Error testing data transformation: {e}")
        return False
    
    # 5. Show available commands
    print("\n5. AVAILABLE COMMANDS")
    print("-" * 30)
    print("To use the full CLI application, you can run:")
    print("  python -m src.main --help")
    print("  python -m src.main preview data/input/sample_locations.json")
    print("  python -m src.main upload data/input/sample_locations.json --validate-only")
    print("  python -m src.main upload data/input/sample_locations.json --aggregator apple")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE!")
    print("The system is ready for bulk location listing management.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = demonstrate_functionality()
    sys.exit(0 if success else 1)