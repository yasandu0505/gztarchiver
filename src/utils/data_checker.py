"""
Data Availability Checker Module
Checks if gazette data is available for specific dates by making HTTP requests.
"""

import requests
from datetime import datetime
from scrapy import Selector
from src.utils.date_utils import parse_date_from_text, matches_date_criteria


class DataAvailabilityChecker:
    """Checks data availability for gazette downloads."""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.download_config = config_loader.get_spider_config('gazette_download')
        self.selectors = self.download_config.get('selectors', {})
        self.request_config = self.download_config.get('request', {})
    
    def check_data_availability(self, year, year_url, month=None, day=None, lang='all'):
        """
        Check if gazettes are available for the specified year/month/day combination.
        Returns True if data is available, False otherwise.
        """
        print(f"🔍 Checking data availability for {year}" + 
              (f"-{month}" if month else "") + 
              (f"-{day}" if day else "") + "...")
        
        try:
            # Get language suffixes to check
            lang_suffixes = self._get_language_suffixes(lang)
            
            # Check each language variant
            for lang_suffix in lang_suffixes:
                if self._check_language_variant(year_url, lang_suffix, year, month, day):
                    print(f"✅ Found matching gazette(s)")
                    return True
            
            # If we get here, no matching dates were found in any language
            return False
            
        except requests.RequestException as e:
            print(f"⚠️ Warning: Could not check data availability (network error): {e}")
            return True  # Fail gracefully
        except Exception as e:
            print(f"⚠️ Warning: Could not validate data availability: {e}")
            return True  # Fail gracefully
    
    def get_available_dates(self, year, year_url, lang='all'):
        """
        Get all available dates for a given year.
        Returns a list of datetime objects representing available dates.
        """
        try:
            # Build URL
            lang_suffix = self._get_single_language_suffix(lang)
            check_url = year_url.rstrip('/') + lang_suffix
            
            # Make request
            response = self._make_request(check_url)
            if not response:
                return []
            
            # Parse response and extract dates
            selector = Selector(text=response.text)
            return self._extract_dates_from_response(selector, year)
            
        except Exception as e:
            print(f"⚠️ Could not fetch available dates: {e}")
            return []
    
    def _get_language_suffixes(self, lang):
        """Get language suffixes based on language parameter."""
        if lang == 'all':
            return ['', '/si', '/ta']  # English, Sinhala, Tamil
        elif lang == 'si':
            return ['/si']
        elif lang == 'ta':
            return ['/ta']
        else:  # 'en' or default
            return ['']
    
    def _get_single_language_suffix(self, lang):
        """Get single language suffix for specific language."""
        if lang == 'si':
            return '/si'
        elif lang == 'ta':
            return '/ta'
        else:
            return ''
    
    def _check_language_variant(self, year_url, lang_suffix, year, month, day):
        """Check a specific language variant for data availability."""
        check_url = year_url.rstrip('/') + lang_suffix
        
        # Make HTTP request
        response = self._make_request(check_url)
        if not response:
            return False
        
        # Parse the response
        selector = Selector(text=response.text)
        
        # Get all table rows
        table_rows_selector = self.selectors.get('table_rows', 'table tbody tr')
        rows = selector.css(table_rows_selector)
        
        if not rows:
            return False
        
        # Check each row for matching dates
        return self._check_rows_for_matches(rows, year, month, day)
    
    def _check_rows_for_matches(self, rows, year, month, day):
        """Check table rows for matching dates."""
        date_selector = self.selectors.get('date', 'td:nth-child(2)::text')
        
        for row in rows:
            try:
                # Extract date text
                date_text = row.css(date_selector).get()
                if not date_text:
                    continue
                
                date_text = date_text.strip()
                
                # Parse the date
                parsed_date = parse_date_from_text(date_text)
                if not parsed_date:
                    continue
                
                # Check if this date matches our criteria
                if matches_date_criteria(parsed_date, year, month, day):
                    # If we're just checking for existence, we can return early
                    if not month and not day:  # Year-only check
                        return True
                    return True
                    
            except Exception:
                # Skip this row if date parsing fails
                continue
        
        return False
    
    def _extract_dates_from_response(self, selector, year):
        """Extract all dates from response for a given year."""
        table_rows_selector = self.selectors.get('table_rows', 'table tbody tr')
        date_selector = self.selectors.get('date', 'td:nth-child(2)::text')
        
        rows = selector.css(table_rows_selector)
        available_dates = []
        
        for row in rows:
            try:
                date_text = row.css(date_selector).get()
                if date_text:
                    parsed_date = parse_date_from_text(date_text.strip())
                    if parsed_date and parsed_date.year == int(year):
                        available_dates.append(parsed_date)
            except:
                continue
        
        return sorted(set(available_dates))  # Remove duplicates and sort
    
    def _make_request(self, url):
        """Make HTTP request with configured settings."""
        headers = self.request_config.get('headers', {})
        timeout = self.request_config.get('timeout', 30)
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException:
            return None