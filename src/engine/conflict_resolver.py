from typing import List, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from sqlalchemy.orm import Session

from ..storage.models import Location, LocationStatus
from ..config.settings import Settings
from ..config.logging_config import get_logger


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving data conflicts"""
    NEWER_WINS = "newer_wins"           # Most recently updated record wins
    OLDER_WINS = "older_wins"           # Oldest record wins
    MANUAL_REVIEW = "manual_review"     # Flag for manual review
    MERGE_FIELDS = "merge_fields"       # Merge non-conflicting fields
    PRIORITY_SOURCE = "priority_source" # Use priority source system


class ConflictType(Enum):
    """Types of data conflicts"""
    DUPLICATE_ID = "duplicate_id"
    DUPLICATE_BUSINESS = "duplicate_business"
    ADDRESS_CONFLICT = "address_conflict"
    PHONE_CONFLICT = "phone_conflict"
    HOURS_CONFLICT = "hours_conflict"
    CATEGORY_CONFLICT = "category_conflict"


@dataclass
class Conflict:
    """Represents a data conflict"""
    conflict_id: str
    conflict_type: ConflictType
    location_ids: List[str]
    conflicting_fields: List[str]
    resolution_strategy: ConflictResolutionStrategy
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class DuplicateGroup:
    """Group of duplicate locations"""
    group_id: str
    location_ids: List[str]
    similarity_score: float
    primary_location_id: Optional[str] = None


class ConflictResolver:
    """Resolves conflicts in location data"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.default_strategy = ConflictResolutionStrategy.NEWER_WINS
    
    def find_duplicates(self, locations: List[Dict[str, Any]]) -> List[DuplicateGroup]:
        """Find duplicate locations in a list"""
        duplicate_groups = []
        processed_ids: Set[str] = set()
        
        for i, location in enumerate(locations):
            if location.get('id') in processed_ids:
                continue
                
            # Find similar locations
            similar_locations = self._find_similar_locations(location, locations[i+1:])
            
            if similar_locations:
                # Create duplicate group
                group_ids = [location['id']] + [loc['id'] for loc in similar_locations]
                similarity_score = self._calculate_similarity_score(location, similar_locations[0])
                
                duplicate_group = DuplicateGroup(
                    group_id=self._generate_group_id(group_ids),
                    location_ids=group_ids,
                    similarity_score=similarity_score
                )
                
                duplicate_groups.append(duplicate_group)
                processed_ids.update(group_ids)
        
        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    def resolve_duplicates(
        self,
        session: Session,
        duplicate_groups: List[DuplicateGroup],
        strategy: Optional[ConflictResolutionStrategy] = None
    ) -> Dict[str, Any]:
        """Resolve duplicate location groups"""
        strategy = strategy or self.default_strategy
        resolved_count = 0
        failed_count = 0
        conflicts_requiring_review = []
        
        for group in duplicate_groups:
            try:
                if strategy == ConflictResolutionStrategy.NEWER_WINS:
                    result = self._resolve_by_newest(session, group)
                elif strategy == ConflictResolutionStrategy.OLDER_WINS:
                    result = self._resolve_by_oldest(session, group)
                elif strategy == ConflictResolutionStrategy.MERGE_FIELDS:
                    result = self._resolve_by_merging(session, group)
                elif strategy == ConflictResolutionStrategy.MANUAL_REVIEW:
                    conflicts_requiring_review.append(group)
                    continue
                else:
                    result = self._resolve_by_newest(session, group)  # Default fallback
                
                if result['success']:
                    resolved_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to resolve duplicate group {group.group_id}: {str(e)}")
                failed_count += 1
        
        return {
            'resolved_groups': resolved_count,
            'failed_groups': failed_count,
            'conflicts_requiring_review': conflicts_requiring_review,
            'resolution_strategy': strategy.value
        }
    
    def detect_field_conflicts(
        self,
        location1: Dict[str, Any],
        location2: Dict[str, Any]
    ) -> List[ConflictType]:
        """Detect conflicts between two locations"""
        conflicts = []
        
        # Check for ID conflicts
        if location1.get('id') == location2.get('id'):
            conflicts.append(ConflictType.DUPLICATE_ID)
        
        # Check for business name conflicts
        if self._business_names_conflict(location1, location2):
            conflicts.append(ConflictType.DUPLICATE_BUSINESS)
        
        # Check for address conflicts
        if self._addresses_conflict(location1, location2):
            conflicts.append(ConflictType.ADDRESS_CONFLICT)
        
        # Check for phone conflicts
        if self._phones_conflict(location1, location2):
            conflicts.append(ConflictType.PHONE_CONFLICT)
        
        # Check for hours conflicts
        if self._hours_conflict(location1, location2):
            conflicts.append(ConflictType.HOURS_CONFLICT)
        
        # Check for category conflicts
        if self._categories_conflict(location1, location2):
            conflicts.append(ConflictType.CATEGORY_CONFLICT)
        
        return conflicts
    
    def _find_similar_locations(
        self,
        target_location: Dict[str, Any],
        locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find locations similar to the target location"""
        similar = []
        threshold = 0.8  # 80% similarity threshold
        
        for location in locations:
            similarity = self._calculate_similarity_score(target_location, location)
            if similarity >= threshold:
                similar.append(location)
        
        return similar
    
    def _calculate_similarity_score(
        self,
        location1: Dict[str, Any],
        location2: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two locations (0.0 to 1.0)"""
        scores = []
        
        # Business name similarity (weight: 0.3)
        name_score = self._calculate_name_similarity(
            location1.get('business_name', ''),
            location2.get('business_name', '')
        )
        scores.append(name_score * 0.3)
        
        # Address similarity (weight: 0.4)
        address_score = self._calculate_address_similarity(location1, location2)
        scores.append(address_score * 0.4)
        
        # Phone similarity (weight: 0.2)
        phone_score = self._calculate_phone_similarity(
            location1.get('phone', ''),
            location2.get('phone', '')
        )
        scores.append(phone_score * 0.2)
        
        # City similarity (weight: 0.1)
        city_score = 1.0 if location1.get('city') == location2.get('city') else 0.0
        scores.append(city_score * 0.1)
        
        return sum(scores)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate business name similarity"""
        if not name1 or not name2:
            return 0.0
        
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        # Exact match
        if name1_clean == name2_clean:
            return 1.0
        
        # Check if one is contained in the other
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.9
        
        # Simple string similarity (can be enhanced with more sophisticated algorithms)
        common_chars = len(set(name1_clean) & set(name2_clean))
        total_chars = len(set(name1_clean) | set(name2_clean))
        
        return common_chars / total_chars if total_chars > 0 else 0.0
    
    def _calculate_address_similarity(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> float:
        """Calculate address similarity"""
        address1 = location1.get('street_address', '').lower().strip()
        address2 = location2.get('street_address', '').lower().strip()
        city1 = location1.get('city', '').lower().strip()
        city2 = location2.get('city', '').lower().strip()
        state1 = location1.get('state', '').lower().strip()
        state2 = location2.get('state', '').lower().strip()
        
        scores = []
        
        # Street address similarity
        if address1 and address2:
            # Simple containment check
            if address1 == address2:
                scores.append(1.0)
            elif address1 in address2 or address2 in address1:
                scores.append(0.8)
            else:
                scores.append(0.3)  # Low score if different
        else:
            scores.append(0.0)
        
        # City similarity
        scores.append(1.0 if city1 == city2 else 0.0)
        
        # State similarity
        scores.append(1.0 if state1 == state2 else 0.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_phone_similarity(self, phone1: str, phone2: str) -> float:
        """Calculate phone number similarity"""
        if not phone1 or not phone2:
            return 0.0
        
        # Normalize phones
        phone1_clean = ''.join(filter(str.isdigit, phone1))
        phone2_clean = ''.join(filter(str.isdigit, phone2))
        
        if phone1_clean == phone2_clean:
            return 1.0
        elif phone1_clean[-10:] == phone2_clean[-10:]:  # Last 10 digits match
            return 0.9
        else:
            return 0.0
    
    def _business_names_conflict(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> bool:
        """Check if business names conflict"""
        name1 = location1.get('business_name', '').lower().strip()
        name2 = location2.get('business_name', '').lower().strip()
        
        return name1 == name2 and name1 != ''
    
    def _addresses_conflict(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> bool:
        """Check if addresses conflict"""
        addr1 = location1.get('street_address', '').lower().strip()
        addr2 = location2.get('street_address', '').lower().strip()
        city1 = location1.get('city', '').lower().strip()
        city2 = location2.get('city', '').lower().strip()
        
        return addr1 == addr2 and city1 == city2 and addr1 != ''
    
    def _phones_conflict(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> bool:
        """Check if phone numbers conflict"""
        phone1 = ''.join(filter(str.isdigit, location1.get('phone', '')))
        phone2 = ''.join(filter(str.isdigit, location2.get('phone', '')))
        
        return phone1 == phone2 and phone1 != ''
    
    def _hours_conflict(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> bool:
        """Check if business hours conflict"""
        hours1 = location1.get('hours')
        hours2 = location2.get('hours')
        
        return hours1 != hours2 and hours1 is not None and hours2 is not None
    
    def _categories_conflict(self, location1: Dict[str, Any], location2: Dict[str, Any]) -> bool:
        """Check if categories conflict"""
        cats1 = set(location1.get('categories', []))
        cats2 = set(location2.get('categories', []))
        
        return cats1 != cats2 and len(cats1) > 0 and len(cats2) > 0
    
    def _resolve_by_newest(self, session: Session, group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve by keeping the newest record"""
        try:
            # Get all locations in the group
            locations = session.query(Location).filter(
                Location.id.in_(group.location_ids)
            ).all()
            
            if not locations:
                return {'success': False, 'error': 'No locations found'}
            
            # Find the newest (most recently updated)
            newest_location = max(locations, key=lambda loc: loc.updated_at)
            
            # Mark others as duplicates
            for location in locations:
                if location.id != newest_location.id:
                    location.status = LocationStatus.FAILED
                    # Add note about duplicate resolution
                    if location.attributes is None:
                        location.attributes = {}
                    location.attributes['duplicate_of'] = newest_location.id
                    location.attributes['resolution_reason'] = 'newer_wins'
            
            session.commit()
            return {'success': True, 'primary_location_id': newest_location.id}
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _resolve_by_oldest(self, session: Session, group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve by keeping the oldest record"""
        try:
            locations = session.query(Location).filter(
                Location.id.in_(group.location_ids)
            ).all()
            
            if not locations:
                return {'success': False, 'error': 'No locations found'}
            
            # Find the oldest
            oldest_location = min(locations, key=lambda loc: loc.created_at)
            
            # Mark others as duplicates
            for location in locations:
                if location.id != oldest_location.id:
                    location.status = LocationStatus.FAILED
                    if location.attributes is None:
                        location.attributes = {}
                    location.attributes['duplicate_of'] = oldest_location.id
                    location.attributes['resolution_reason'] = 'older_wins'
            
            session.commit()
            return {'success': True, 'primary_location_id': oldest_location.id}
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _resolve_by_merging(self, session: Session, group: DuplicateGroup) -> Dict[str, Any]:
        """Resolve by merging non-conflicting fields"""
        try:
            locations = session.query(Location).filter(
                Location.id.in_(group.location_ids)
            ).all()
            
            if not locations:
                return {'success': False, 'error': 'No locations found'}
            
            # Create merged location (keep the first one as base)
            primary_location = locations[0]
            
            # Merge fields from other locations
            for location in locations[1:]:
                # Merge phone if primary doesn't have one
                if not primary_location.phone and location.phone:
                    primary_location.phone = location.phone
                
                # Merge website if primary doesn't have one
                if not primary_location.website and location.website:
                    primary_location.website = location.website
                
                # Merge categories (union)
                if location.categories:
                    current_categories = primary_location.categories or []
                    merged_categories = list(set(current_categories + location.categories))
                    primary_location.categories = merged_categories[:10]  # Limit to 10
                
                # Mark as duplicate
                location.status = LocationStatus.FAILED
                if location.attributes is None:
                    location.attributes = {}
                location.attributes['merged_into'] = primary_location.id
                location.attributes['resolution_reason'] = 'merged_fields'
            
            session.commit()
            return {'success': True, 'primary_location_id': primary_location.id}
            
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _generate_group_id(self, location_ids: List[str]) -> str:
        """Generate unique group ID for duplicate group"""
        sorted_ids = sorted(location_ids)
        ids_string = ','.join(sorted_ids)
        return hashlib.md5(ids_string.encode()).hexdigest()[:12]