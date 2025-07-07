"""
Date Utils Module
Provides date parsing and matching utilities for gazette data.
"""

import re
from datetime import datetime


def parse_date_from_text(date_text):
    """
    Parse date from various text formats commonly found in gazette tables.
    Returns a datetime object or None if parsing fails.
    """
    if not date_text:
        return None
    
    date_text = date_text.strip()
    
    # Common date patterns to try
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-12-25
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 25/12/2023
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 25-12-2023
        r'(\d{4})\.(\d{1,2})\.(\d{1,2})', # 2023.12.25
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})', # 25.12.2023
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_text)
        if match:
            try:
                groups = match.groups()
                
                # Determine if it's YYYY-MM-DD or DD-MM-YYYY format
                if len(groups[0]) == 4:  # Year first
                    year, month, day = groups
                else:  # Day first
                    day, month, year = groups
                
                return datetime(int(year), int(month), int(day))
            except (ValueError, IndexError):
                continue
    
    return None


def matches_date_criteria(parsed_date, target_year, target_month=None, target_day=None):
    """
    Check if a parsed date matches the given criteria.
    """
    # Check year
    if parsed_date.year != int(target_year):
        return False
    
    # Check month if specified
    if target_month is not None:
        if parsed_date.month != int(target_month):
            return False
    
    # Check day if specified
    if target_day is not None:
        if parsed_date.day != int(target_day):
            return False
    
    return True