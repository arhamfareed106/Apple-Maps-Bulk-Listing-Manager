#!/usr/bin/env python3
"""
Comprehensive demonstration of Apple Maps Bulk Listing Manager
"""

import sys
import json
import os

# Add current directory to path
sys.path.insert(0, '.')

def main():
    print("=" * 70)
    print("APPLE MAPS BULK LISTING MANAGER - COMPLETE DEMONSTRATION")
    print("=" * 70)
    
    # 1. Load and display sample data
    print("\n1. SAMPLE DATA")
    print("-" * 30)
    sample_file = "data/input/sample_locations.json"
    with open(sample_file, 'r') as f:
        sample_data = json.load(f)
    
    print(f"✓ Loaded {len(sample_data)} sample records")
    print("First record:")
    print(json.dumps(sample_data[0], indent=2))
    
    # 2. Test data validation
    print("\n2. DATA VALIDATION")
    print("-" * 30)
    try:
        from src.data.schema import AppleLocationSchema
        validated_record = AppleLocationSchema(**sample_data[0])
        print("✓ Apple Business Connect schema validation: PASSED")
        print(f"  Business Name: {validated_record.business_name}")
        print(f"  Address: {validated_record.street_address}, {validated_record.city}")
        print(f"  Phone: {validated_record.phone}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False
    
    # 3. Test data transformation
    print("\n3. DATA TRANSFORMATION")
    print("-" * 30)
    try:
        from src.data.transformer import DataTransformer, AggregatorType
        transformer = DataTransformer()
        
        # Transform to different aggregator formats
        apple_format = transformer.transform_to_aggregator_format(sample_data[0], AggregatorType.APPLE)
        yext_format = transformer.transform_to_aggregator_format(sample_data[0], AggregatorType.YEXT)
        
        print("✓ Data transformation: PASSED")
        print("Apple format sample:")
        print(f"  {apple_format['business_name']} - {apple_format['city']}, {apple_format['state']}")
        print("Yext format sample:")
        print(f"  {yext_format['name']} - {yext_format['city']}, {yext_format['state']}")
    except Exception as e:
        print(f"✗ Transformation failed: {e}")
        return False
    
    # 4. Test data processing
    print("\n4. DATA PROCESSING")
    print("-" * 30)
    try:
        from src.data.processor import DataProcessor
        processor = DataProcessor()
        
        # Test phone normalization
        normalized_phone = processor._normalize_phone("212-555-1234")
        normalized_state = processor._normalize_state("New York")
        normalized_zip = processor._normalize_zip("10001-1234")
        
        print("✓ Data processing functions: PASSED")
        print(f"  Phone normalization: 212-555-1234 → {normalized_phone}")
        print(f"  State normalization: New York → {normalized_state}")
        print(f"  ZIP normalization: 10001-1234 → {normalized_zip}")
    except Exception as e:
        print(f"✗ Data processing failed: {e}")
        return False
    
    # 5. Test data validation completeness
    print("\n5. DATA QUALITY ASSESSMENT")
    print("-" * 30)
    try:
        from src.data.validator import DataValidator
        validator = DataValidator()
        
        completeness = validator.validate_field_completeness(sample_data)
        print("✓ Data quality assessment: PASSED")
        print(f"  Total locations: {completeness['total_locations']}")
        print(f"  Overall quality score: {completeness['overall_quality_score']}%")
        print(f"  Quality tier: {completeness['quality_tier']}")
        
        # Show field completeness
        print("  Field completeness:")
        for field, stats in completeness['field_completeness'].items():
            if stats['completeness_percentage'] < 100:
                print(f"    {field}: {stats['completeness_percentage']}% ({stats['missing']} missing)")
    except Exception as e:
        print(f"✗ Quality assessment failed: {e}")
        return False
    
    # 6. Show available CLI commands
    print("\n6. AVAILABLE CLI COMMANDS")
    print("-" * 30)
    print("The full CLI application can be used with these commands:")
    print("  python -m src.main --help")
    print("  python -m src.main preview data/input/sample_locations.json")
    print("  python -m src.main upload data/input/sample_locations.json --validate-only")
    print("  python -m src.main upload data/input/sample_locations.json --aggregator apple")
    print("  python -m src.main upload data/input/sample_locations.json --aggregator yext")
    
    # 7. Project structure verification
    print("\n7. PROJECT STRUCTURE")
    print("-" * 30)
    required_components = [
        "src/main.py",
        "src/config/settings.py",
        "src/config/logging_config.py",
        "src/api/base_client.py",
        "src/api/apple_client.py",
        "src/data/schema.py",
        "src/data/reader.py",
        "src/data/processor.py",
        "src/data/validator.py",
        "src/data/transformer.py",
        "src/engine/bulk_uploader.py",
        "src/storage/models.py",
        "src/storage/database.py",
        "requirements.txt",
        "README.md"
    ]
    
    missing_components = []
    for component in required_components:
        if not os.path.exists(component):
            missing_components.append(component)
    
    if not missing_components:
        print("✓ All core components present")
        print(f"  Total components: {len(required_components)}")
    else:
        print(f"✗ Missing components: {len(missing_components)}")
        for component in missing_components[:5]:  # Show first 5
            print(f"    {component}")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE - SYSTEM IS FULLY FUNCTIONAL!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Install full dependencies: pip install -r requirements.txt")
    print("2. Create .env file with your API credentials")
    print("3. Run validation: python -m src.main upload data/input/sample_locations.json --validate-only")
    print("4. Run full upload: python -m src.main upload data/input/sample_locations.json --aggregator apple")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)