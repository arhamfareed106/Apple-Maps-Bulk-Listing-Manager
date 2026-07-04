import pandas as pd
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
import usaddress

from .schema import LocationSchema, AppleLocationSchema
from ..config.logging_config import get_logger


class DataProcessor:
    """Process and clean location data"""
    
    def __init__(self):
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._setup_normalization_rules()
    
    def _setup_normalization_rules(self):
        """Setup data normalization rules"""
        self.phone_patterns = [
            (r'\D', ''),  # Remove all non-digits
        ]
        
        self.state_mapping = {
            'AL': 'AL', 'Alabama': 'AL',
            'AK': 'AK', 'Alaska': 'AK',
            'AZ': 'AZ', 'Arizona': 'AZ',
            'AR': 'AR', 'Arkansas': 'AR',
            'CA': 'CA', 'California': 'CA',
            'CO': 'CO', 'Colorado': 'CO',
            'CT': 'CT', 'Connecticut': 'CT',
            'DE': 'DE', 'Delaware': 'DE',
            'FL': 'FL', 'Florida': 'FL',
            'GA': 'GA', 'Georgia': 'GA',
            'HI': 'HI', 'Hawaii': 'HI',
            'ID': 'ID', 'Idaho': 'ID',
            'IL': 'IL', 'Illinois': 'IL',
            'IN': 'IN', 'Indiana': 'IN',
            'IA': 'IA', 'Iowa': 'IA',
            'KS': 'KS', 'Kansas': 'KS',
            'KY': 'KY', 'Kentucky': 'KY',
            'LA': 'LA', 'Louisiana': 'LA',
            'ME': 'ME', 'Maine': 'ME',
            'MD': 'MD', 'Maryland': 'MD',
            'MA': 'MA', 'Massachusetts': 'MA',
            'MI': 'MI', 'Michigan': 'MI',
            'MN': 'MN', 'Minnesota': 'MN',
            'MS': 'MS', 'Mississippi': 'MS',
            'MO': 'MO', 'Missouri': 'MO',
            'MT': 'MT', 'Montana': 'MT',
            'NE': 'NE', 'Nebraska': 'NE',
            'NV': 'NV', 'Nevada': 'NV',
            'NH': 'NH', 'New Hampshire': 'NH',
            'NJ': 'NJ', 'New Jersey': 'NJ',
            'NM': 'NM', 'New Mexico': 'NM',
            'NY': 'NY', 'New York': 'NY',
            'NC': 'NC', 'North Carolina': 'NC',
            'ND': 'ND', 'North Dakota': 'ND',
            'OH': 'OH', 'Ohio': 'OH',
            'OK': 'OK', 'Oklahoma': 'OK',
            'OR': 'OR', 'Oregon': 'OR',
            'PA': 'PA', 'Pennsylvania': 'PA',
            'RI': 'RI', 'Rhode Island': 'RI',
            'SC': 'SC', 'South Carolina': 'SC',
            'SD': 'SD', 'South Dakota': 'SD',
            'TN': 'TN', 'Tennessee': 'TN',
            'TX': 'TX', 'Texas': 'TX',
            'UT': 'UT', 'Utah': 'UT',
            'VT': 'VT', 'Vermont': 'VT',
            'VA': 'VA', 'Virginia': 'VA',
            'WA': 'WA', 'Washington': 'WA',
            'WV': 'WV', 'West Virginia': 'WV',
            'WI': 'WI', 'Wisconsin': 'WI',
            'WY': 'WY', 'Wyoming': 'WY'
        }
    
    def process_dataframe(self, df: pd.DataFrame, source_type: str = 'generic') -> List[Dict[str, Any]]:
        """Process pandas DataFrame into standardized location data"""
        processed_data = []
        
        # Clean column names
        df = self._clean_column_names(df)
        
        # Normalize data
        df = self._normalize_data(df)
        
        # Process each row
        for index, row in df.iterrows():
            try:
                location_data = self._process_row(row, source_type)
                if location_data:
                    processed_data.append(location_data)
            except Exception as e:
                self.logger.warning(f"Failed to process row {index}: {str(e)}")
                continue
        
        self.logger.info(f"Processed {len(processed_data)} locations from {len(df)} rows")
        return processed_data
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names"""
        # Convert to lowercase and replace spaces/underscores
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Create mapping for common column variations
        column_mapping = {
            'name': ['business_name', 'company_name', 'store_name', 'location_name'],
            'address': ['street_address', 'address_line_1', 'street', 'address1'],
            'city': ['city', 'town'],
            'state': ['state', 'state_province', 'province'],
            'zip': ['postal_code', 'zip_code', 'zipcode', 'zip'],
            'phone': ['phone_number', 'phone', 'telephone'],
            'website': ['website_url', 'url', 'website'],
            'email': ['email_address', 'email']
        }
        
        # Apply column mapping
        for standard_name, variations in column_mapping.items():
            for variation in variations:
                if variation in df.columns and standard_name not in df.columns:
                    df.rename(columns={variation: standard_name}, inplace=True)
                    break
        
        return df
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize data in the dataframe"""
        # Normalize phone numbers
        if 'phone' in df.columns:
            df['phone'] = df['phone'].apply(self._normalize_phone)
        
        # Normalize state names
        if 'state' in df.columns:
            df['state'] = df['state'].apply(self._normalize_state)
        
        # Normalize ZIP codes
        if 'zip' in df.columns:
            df['zip'] = df['zip'].apply(self._normalize_zip)
        
        # Clean business names
        if 'name' in df.columns:
            df['name'] = df['name'].apply(self._clean_business_name)
        
        # Validate and clean addresses
        if 'address' in df.columns:
            df['address'] = df['address'].apply(self._clean_address)
        
        return df
    
    def _process_row(self, row: pd.Series, source_type: str) -> Optional[Dict[str, Any]]:
        """Process a single row into location data"""
        try:
            # Extract basic information
            location_data = {
                'business_name': str(row.get('name', '')).strip(),
                'street_address': str(row.get('address', '')).strip(),
                'city': str(row.get('city', '')).strip(),
                'state': str(row.get('state', '')).strip(),
                'postal_code': str(row.get('zip', '')).strip(),
                'country': 'US'
            }
            
            # Add optional fields
            if 'phone' in row and pd.notna(row['phone']):
                location_data['phone'] = str(row['phone']).strip()
            
            if 'website' in row and pd.notna(row['website']):
                website = str(row['website']).strip()
                if not website.startswith(('http://', 'https://')):
                    website = f"https://{website}"
                location_data['website'] = website
            
            if 'email' in row and pd.notna(row['email']):
                location_data['email'] = str(row['email']).strip()
            
            # Validate required fields
            if not all([location_data.get('business_name'), 
                       location_data.get('street_address'),
                       location_data.get('city'),
                       location_data.get('state'),
                       location_data.get('postal_code')]):
                self.logger.warning(f"Missing required fields: {location_data}")
                return None
            
            # Validate using schema
            location_schema = LocationSchema(**location_data)
            return location_schema.model_dump()
            
        except Exception as e:
            self.logger.warning(f"Failed to process row: {str(e)}")
            return None
    
    def _normalize_phone(self, phone: Any) -> str:
        """Normalize phone number to E.164 format"""
        if pd.isna(phone) or phone == '':
            return ''
        
        phone_str = str(phone)
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_str)
        
        # Convert to E.164 format
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif len(digits) == 12 and digits.startswith('+'):
            return digits
        else:
            # Return original if format is unclear
            return phone_str
    
    def _normalize_state(self, state: Any) -> str:
        """Normalize state to 2-letter abbreviation"""
        if pd.isna(state) or state == '':
            return ''
        
        state_str = str(state).strip()
        
        # Check if already 2-letter abbreviation
        if len(state_str) == 2 and state_str.isalpha():
            return state_str.upper()
        
        # Look up in mapping
        normalized = self.state_mapping.get(state_str.title())
        if normalized:
            return normalized
        
        # Return original if not found
        return state_str.upper()
    
    def _normalize_zip(self, zip_code: Any) -> str:
        """Normalize ZIP code format"""
        if pd.isna(zip_code) or zip_code == '':
            return ''
        
        zip_str = str(zip_code).strip()
        
        # Remove non-digits
        digits = re.sub(r'\D', '', zip_str)
        
        # Format based on length
        if len(digits) == 5:
            return digits
        elif len(digits) == 9:
            return f"{digits[:5]}-{digits[5:]}"
        else:
            return zip_str
    
    def _clean_business_name(self, name: Any) -> str:
        """Clean business name"""
        if pd.isna(name) or name == '':
            return ''
        
        name_str = str(name).strip()
        
        # Remove extra whitespace and standardize
        name_str = re.sub(r'\s+', ' ', name_str)
        
        # Remove common suffixes that might be data artifacts
        suffixes_to_remove = ['LLC', 'INC', 'CORP', 'LTD', 'LIMITED']
        for suffix in suffixes_to_remove:
            pattern = rf'\s+{suffix}\.?$', re.IGNORECASE
            name_str = re.sub(rf'\s+{suffix}\.?$', '', name_str, flags=re.IGNORECASE)
        
        return name_str.strip()
    
    def _clean_address(self, address: Any) -> str:
        """Clean address string"""
        if pd.isna(address) or address == '':
            return ''
        
        address_str = str(address).strip()
        
        # Remove extra whitespace
        address_str = re.sub(r'\s+', ' ', address_str)
        
        # Standardize common abbreviations
        abbreviations = {
            'ST': 'Street',
            'AVE': 'Avenue', 
            'RD': 'Road',
            'BLVD': 'Boulevard',
            'DR': 'Drive',
            'LN': 'Lane',
            'CT': 'Court',
            'PL': 'Place',
            'HWY': 'Highway'
        }
        
        for abbr, full in abbreviations.items():
            address_str = re.sub(rf'\b{abbr}\b', full, address_str, flags=re.IGNORECASE)
        
        return address_str.strip()
    
    def validate_location_data(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location data using schema"""
        try:
            # Validate with LocationSchema
            validated = LocationSchema(**location_data)
            return validated.model_dump()
        except Exception as e:
            self.logger.error(f"Validation failed for location data: {str(e)}")
            raise
    
    def transform_for_apple(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform location data for Apple Business Connect API"""
        try:
            # Map fields to Apple format
            apple_data = {
                'business_name': location_data['business_name'],
                'street_address': location_data['street_address'],
                'city': location_data['city'],
                'state': location_data['state'],
                'postal_code': location_data['postal_code'],
                'country': location_data.get('country', 'US')
            }
            
            # Add optional fields
            if location_data.get('phone'):
                apple_data['phone'] = location_data['phone']
            
            if location_data.get('website'):
                apple_data['website'] = location_data['website']
            
            # Validate with Apple schema
            validated = AppleLocationSchema(**apple_data)
            return validated.model_dump()
            
        except Exception as e:
            self.logger.error(f"Failed to transform for Apple: {str(e)}")
            raise