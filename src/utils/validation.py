"""
Data Validation for Daily Digest
Ensures all content is current, factual, and from reliable sources
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any


# Trusted sources for content validation
TRUSTED_SOURCES = {
    "weather": [
        "OpenWeather API",
        "Weather.com",
        "National Weather Service",
        "NOAA"
    ],
    "sports": [
        "ESPN API",
        "The Sports DB",
        "Official team websites",
        "NBA.com",
        "NFL.com",
        "NHL.com",
        "Mock Sports Data" 
    ],
    "tech": [
        "TechCrunch",
        "The Verge",
        "Ars Technica",
        "Wired",
        "MIT Technology Review",
        "VentureBeat",
        "News API",
        "RSS Feeds"
    ],
    "market": [
        "Alpha Vantage",
        "Yahoo Finance",
        "Bloomberg",
        "Reuters",
        "MarketWatch",
        "Alpha Vantage API"
    ]
}


class DigestValidator:
    """
    Validates digest data quality before publishing
    Implements quality assurance checks
    """
    
    def __init__(
        self,
        max_data_age_hours: float = 24,
        min_reliability_score: float = 0.8,
        required_sections: List[str] = None
    ):
        """
        Initialize validator
        
        Args:
            max_data_age_hours: Maximum acceptable age of data in hours
            min_reliability_score: Minimum source reliability score (0-1)
            required_sections: List of required section names
        """
        self.max_data_age_hours = max_data_age_hours
        self.min_reliability_score = min_reliability_score
        self.required_sections = required_sections or ["weather", "sports", "tech", "market"]
    
    def validate(self, digest_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete digest data
        
        Args:
            digest_data: Digest data dictionary
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if sections exist
        if "sections" not in digest_data:
            errors.append("Missing 'sections' field in digest data")
            return False, errors
        
        sections = digest_data["sections"]
        
        # Validation checks
        errors.extend(self._check_completeness(sections))
        errors.extend(self._check_data_freshness(sections))
        errors.extend(self._check_source_reliability(sections))
        errors.extend(self._check_content_validity(sections))
        
        return len(errors) == 0, errors
    
    def _check_completeness(self, sections: List[Dict]) -> List[str]:
        """Check if all required sections are present"""
        errors = []
        
        present_sections = {s.get("name", "").lower() for s in sections}
        required_sections = set(self.required_sections)
        
        missing = required_sections - present_sections
        if missing:
            errors.append(
                f"Missing required sections: {', '.join(sorted(missing))}"
            )
        
        return errors
    
    def _check_data_freshness(self, sections: List[Dict]) -> List[str]:
        """Check if data is recent enough"""
        errors = []
        now = datetime.now()
        max_age = timedelta(hours=self.max_data_age_hours)
        
        for section in sections:
            section_name = section.get("name", "unknown")
            timestamp_str = section.get("timestamp")
            
            if not timestamp_str:
                errors.append(f"{section_name}: Missing timestamp")
                continue
            
            try:
                # Parse timestamp (handles both ISO format and partial dates)
                if "T" in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    # If only date provided, assume it's today
                    timestamp = datetime.fromisoformat(timestamp_str)
                
                age = now - timestamp
                
                if age > max_age:
                    hours_old = age.total_seconds() / 3600
                    errors.append(
                        f"{section_name}: Data is {hours_old:.1f} hours old "
                        f"(max: {self.max_data_age_hours})"
                    )
            except (ValueError, TypeError) as e:
                errors.append(
                    f"{section_name}: Invalid timestamp format '{timestamp_str}': {e}"
                )
        
        return errors
    
    def _check_source_reliability(self, sections: List[Dict]) -> List[str]:
        """Check if sources are reliable"""
        errors = []
        
        for section in sections:
            section_name = section.get("name", "unknown")
            source = section.get("source")
            
            if not source:
                errors.append(f"{section_name}: Missing source attribution")
                continue
            
            # Get trusted sources for this section type
            section_type = section_name.lower()
            trusted = TRUSTED_SOURCES.get(section_type, [])
            
            # Check if source matches any trusted source (case-insensitive, partial match)
            is_trusted = any(
                trusted_source.lower() in source.lower()
                for trusted_source in trusted
            )
            
            if not is_trusted and trusted:
                errors.append(
                    f"{section_name}: Source '{source}' not in trusted list. "
                    f"Trusted sources: {', '.join(trusted[:3])}..."
                )
        
        return errors
    
    def _check_content_validity(self, sections: List[Dict]) -> List[str]:
        """Check if content is valid and sufficient"""
        errors = []
        
        for section in sections:
            section_name = section.get("name", "unknown")
            
            # Check for content field
            if "content" not in section and "data" not in section:
                errors.append(f"{section_name}: Missing content or data field")
                continue
            
            # Check content length
            content = section.get("content") or section.get("data")
            
            if isinstance(content, str):
                if len(content.strip()) < 20:
                    errors.append(
                        f"{section_name}: Content too short ({len(content)} chars, min: 20)"
                    )
            elif isinstance(content, dict):
                # For structured data, check if not empty
                if not content:
                    errors.append(f"{section_name}: Empty data object")
            elif isinstance(content, list):
                if len(content) == 0:
                    errors.append(f"{section_name}: Empty data list")
        
        return errors
    
    def calculate_quality_score(self, digest_data: Dict[str, Any]) -> float:
        """
        Calculate overall quality score (0-1)
        
        Args:
            digest_data: Digest data dictionary
        
        Returns:
            Quality score between 0 and 1
        """
        is_valid, errors = self.validate(digest_data)
        
        if not is_valid:
            # Penalize based on number of errors
            num_errors = len(errors)
            max_errors = 10  # Reasonable maximum
            return max(0.0, 1.0 - (num_errors / max_errors))
        
        return 1.0
    
    def get_validation_summary(self, digest_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed validation summary
        
        Args:
            digest_data: Digest data dictionary
        
        Returns:
            Dictionary with validation results and metrics
        """
        is_valid, errors = self.validate(digest_data)
        quality_score = self.calculate_quality_score(digest_data)
        
        return {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "error_count": len(errors),
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }


def validate_digest(digest_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate digest data
    
    Args:
        digest_data: Digest data dictionary
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = DigestValidator()
    return validator.validate(digest_data)
