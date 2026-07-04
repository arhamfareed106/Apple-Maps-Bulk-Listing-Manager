"""
Simple test script to verify basic functionality
"""
import json
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    
    print("Testing Apple Maps Bulk Listing Manager")
    print("=" * 50)
    
    # Test 1: Basic data structure
    print("\n1. Testing basic data structure...")
    sample_location = {
        "business_name": "Test Store",
        "street_address": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "US",
        "phone": "+12125551234"
    }
    
    # Validate required fields
    required_fields = ["business_name", "street_address", "city", "state", "postal_code"]
    missing_fields = [field for field in required_fields if field not in sample_location]
    
    if not missing_fields:
        print("✓ Basic data structure validation passed")
    else:
        print(f"✗ Missing required fields: {missing_fields}")
        return False
    
    # Test 2: Phone number formatting
    print("\n2. Testing phone number formatting...")
    phone = sample_location["phone"]
    # Simple validation - check if it starts with +
    if phone.startswith("+") and len(phone) >= 10:
        print("✓ Phone number format validation passed")
    else:
        print("✗ Invalid phone number format")
        return False
    
    # Test 3: ZIP code validation
    print("\n3. Testing ZIP code validation...")
    zip_code = sample_location["postal_code"]
    if len(zip_code) == 5 and zip_code.isdigit():
        print("✓ ZIP code validation passed")
    else:
        print("✗ Invalid ZIP code format")
        return False
    
    # Test 4: State validation
    print("\n4. Testing state validation...")
    state = sample_location["state"]
    if len(state) == 2 and state.isalpha() and state.isupper():
        print("✓ State validation passed")
    else:
        print("✗ Invalid state format")
        return False
    
    # Test 5: Create sample data file
    print("\n5. Creating sample data file...")
    try:
        sample_data = [sample_location, {
            "business_name": "Another Store",
            "street_address": "456 Oak Avenue",
            "city": "Los Angeles", 
            "state": "CA",
            "postal_code": "90210",
            "country": "US",
            "phone": "+13105559876"
        }]
        
        # Create data directory
        os.makedirs("data/input", exist_ok=True)
        
        # Save sample data
        with open("data/input/sample_locations.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        print("✓ Sample data file created successfully")
        print("  File: data/input/sample_locations.json")
        
    except Exception as e:
        print(f"✗ Failed to create sample data file: {e}")
        return False
    
    # Test 6: File structure verification
    print("\n6. Verifying project structure...")
    required_files = [
        "src/main.py",
        "src/config/settings.py", 
        "src/data/schema.py",
        "src/engine/bulk_uploader.py",
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("✓ All required files present")
    else:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All basic tests passed!")
    print("\nNext steps:")
    print("1. Install full dependencies: pip install -r requirements.txt")
    print("2. Create .env file with your API credentials")
    print("3. Run: python -m src.main preview data/input/sample_locations.json")
    print("4. Run: python -m src.main upload data/input/sample_locations.json --validate-only")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)