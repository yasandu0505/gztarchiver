import json
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_download import GazetteDownloadSpider
from gazette_tracker.spiders.gazette_years import GazetteYearsSpider
from scrapy.utils.log import configure_logging
from config_loader import ConfigLoader 
import logging
import sys
import os
import requests
from datetime import datetime
import re
from scrapy import Selector
import warnings

warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')


def create_cli_parser(config_loader):
    """Create CLI argument parser with defaults from config"""
    cli_defaults = config_loader.get_cli_defaults()
    
    parser = argparse.ArgumentParser(description="Download gazettes by year and language.")
    parser.add_argument("--year", 
                       default=cli_defaults.get('year', 'all'), 
                       help="Year to download (e.g., 2023 or 'all'). Default from config.")
    parser.add_argument("--month", 
                       default=cli_defaults.get('month'), 
                       help="Month to download (e.g., 01, 12). Optional.")
    parser.add_argument("--day", 
                       default=cli_defaults.get('day'), 
                       help="Day to download (e.g., 01, 31). Optional.")
    parser.add_argument("--lang", 
                       default=cli_defaults.get('language', 'all'), 
                       help="Language: en (English), si (Sinhala), ta (Tamil), or all. Default from config.")
    parser.add_argument("--c_logs", 
                       default='Y' if cli_defaults.get('enable_scrapy_logs', False) else 'N', 
                       help="Enable Scrapy logs (Y/N). Default from config.")
    parser.add_argument("--update_years", 
                       action="store_true", 
                       help="Update years.json by scraping the website first.")
    parser.add_argument("--config", 
                       default="config.yaml", 
                       help="Path to configuration file. Default: config.yaml")
    parser.add_argument("--show_config", 
                       action="store_true", 
                       help="Show current configuration and exit.")
    
    return parser

def configure_scrapy_logging(config_loader, enable_logs):
    """Configure Scrapy logging based on config and CLI args"""
    scrapy_settings = config_loader.get_scrapy_settings()
    
    if enable_logs.upper() != "Y":
        log_level = scrapy_settings.get('LOG_LEVEL', 'ERROR')
        log_format = scrapy_settings.get('LOG_FORMAT', '%(levelname)s: %(message)s')
        log_stdout = scrapy_settings.get('LOG_STDOUT', False)
        
        configure_logging({
            'LOG_LEVEL': log_level,
            'LOG_FORMAT': log_format,
            'LOG_STDOUT': log_stdout
        })
        logging.getLogger('scrapy').propagate = False

def update_years_json(config_loader):
    """Update years.json using GazetteYearsSpider with config"""
    print("\n🔄 Fetching years data from website...")
    
    # Get spider configuration
    years_config = config_loader.get_spider_config('gazette_years')
    scrapy_settings = config_loader.get_scrapy_settings()
    
    # Create process settings
    years_settings = get_project_settings()
    
    # Apply scrapy settings from config
    for key, value in scrapy_settings.items():
        years_settings.set(key, value)
    
    years_process = CrawlerProcess(years_settings)
    
    # Get output settings from config
    output_config = years_config.get('output', {})
    save_to_file = output_config.get('save_to_file', True)
    
    # Configure and start the GazetteYearsSpider
    years_process.crawl(GazetteYearsSpider, 
                       config=years_config,  # Pass config to spider
                       save_to_file=save_to_file)
    years_process.start()
    
    # Check if years.json was created/updated
    filename = output_config.get('filename', 'years.json')
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                year_data = json.load(f)
            if year_data:
                print(f"✅ Successfully updated {filename} with {len(year_data)} years")
                return year_data
            else:
                print(f"⚠️ {filename} was created but is empty")
                return None
        except json.JSONDecodeError:
            print(f"❌ Error: Invalid JSON format in {filename}")
            return None
    else:
        print(f"❌ Failed to create {filename}")
        return None

def load_year_data(config_loader):
    """Load year data from years.json or return None if not found."""
    years_config = config_loader.get_spider_config('gazette_years')
    filename = years_config.get('output', {}).get('filename', 'years.json')
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"\n❌ Error: Invalid JSON format in {filename}.")
        sys.exit(1)

def get_year_entry(year_data, year):
    """Helper: fetch year entry from year data"""
    return next((item for item in year_data if item["year"] == year), None)

def validate_date_inputs(month, day):
    """Validate month and day inputs"""
    if month:
        try:
            month_int = int(month)
            if month_int < 1 or month_int > 12:
                print(f"\n❌ Invalid month '{month}'. Must be between 01-12.")
                sys.exit(1)
            month = f"{month_int:02d}"
        except ValueError:
            print(f"\n❌ Invalid month format '{month}'. Use format: 01, 02, ..., 12.")
            sys.exit(1)
    
    if day:
        try:
            day_int = int(day)
            if day_int < 1 or day_int > 31:
                print(f"\n❌ Invalid day '{day}'. Must be between 01-31.")
                sys.exit(1)
            day = f"{day_int:02d}"
        except ValueError:
            print(f"\n❌ Invalid day format '{day}'. Use format: 01, 02, ..., 31.")
            sys.exit(1)
    
    return month, day

def check_data_availability(config_loader, year, year_url, month=None, day=None, lang='all'):
    """
    Check if gazettes are available for the specified year/month/day combination
    by making a lightweight HTTP request and parsing the table data.
    Returns True if data is available, False otherwise.
    """
    print(f"🔍 Checking data availability for {year}" + 
          (f"-{month}" if month else "") + 
          (f"-{day}" if day else "") + "...")
    
    try:
        # Get selectors from config
        download_config = config_loader.get_spider_config('gazette_download')
        selectors = download_config.get('selectors', {})
        
        # Required selectors
        table_rows_selector = selectors.get('table_rows', 'table tbody tr')
        date_selector = selectors.get('date', 'td:nth-child(2)::text')
        
        # Get request settings from config
        request_config = download_config.get('request', {})
        headers = request_config.get('headers', {})
        timeout = request_config.get('timeout', 30)
        
        # Build the URL based on language
        if lang == 'all':
            # Check all languages - start with English as default
            lang_suffixes = ['', '/si', '/ta']  # English, Sinhala, Tamil
        elif lang == 'si':
            lang_suffixes = ['/si']
        elif lang == 'ta':
            lang_suffixes = ['/ta']
        else:  # 'en' or default
            lang_suffixes = ['']
        
        # Check each language variant
        for lang_suffix in lang_suffixes:
            check_url = year_url.rstrip('/') + lang_suffix
            
            # Make HTTP request
            response = requests.get(check_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Parse the response with Scrapy's Selector
            selector = Selector(text=response.text)
            
            # Get all table rows
            rows = selector.css(table_rows_selector)
            
            if not rows:
                continue  # Try next language if no rows found
            
            # Extract dates from each row
            found_matching_dates = []
            
            for row in rows:
                try:
                    # Extract date text
                    date_text = row.css(date_selector).get()
                    if not date_text:
                        continue
                    
                    date_text = date_text.strip()
                    
                    # Parse the date - assuming format like "2023-12-25" or "25/12/2023" etc.
                    parsed_date = parse_date_from_text(date_text)
                    if not parsed_date:
                        continue
                    
                    # Check if this date matches our criteria
                    if matches_date_criteria(parsed_date, year, month, day):
                        found_matching_dates.append(parsed_date)
                        
                        # If we're just checking for existence, we can return early
                        if not month and not day:  # Year-only check
                            return True
                
                except Exception as e:
                    # Skip this row if date parsing fails
                    continue
            
            # Check if we found any matching dates
            if found_matching_dates:
                print(f"✅ Found {len(found_matching_dates)} matching gazette(s)")
                return True
        
        # If we get here, no matching dates were found in any language
        return False
        
    except requests.RequestException as e:
        print(f"⚠️ Warning: Could not check data availability (network error): {e}")
        # If network fails, proceed anyway (fail gracefully)
        return True
    except Exception as e:
        print(f"⚠️ Warning: Could not validate data availability: {e}")
        # If validation fails, proceed anyway (fail gracefully)
        return True

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

# Alternative function if you want to get all available dates for better user feedback
def get_available_dates(config_loader, year, year_url, lang='all'):
    """
    Get all available dates for a given year to provide better user feedback.
    Returns a list of datetime objects representing available dates.
    """
    try:
        # Get selectors from config
        download_config = config_loader.get_spider_config('gazette_download')
        selectors = download_config.get('selectors', {})
        
        table_rows_selector = selectors.get('table_rows', 'table tbody tr')
        date_selector = selectors.get('date', 'td:nth-child(2)::text')
        
        # Get request settings
        request_config = download_config.get('request', {})
        headers = request_config.get('headers', {})
        timeout = request_config.get('timeout', 30)
        
        # Build URL
        lang_suffix = '/si' if lang == 'si' else '/ta' if lang == 'ta' else ''
        check_url = year_url.rstrip('/') + lang_suffix
        
        # Make request
        response = requests.get(check_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse response
        selector = Selector(text=response.text)
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
        
    except Exception as e:
        print(f"⚠️ Could not fetch available dates: {e}")
        return []

def create_download_process(config_loader):
    """Create CrawlerProcess with settings from config"""
    base_settings = get_project_settings()
    scrapy_settings = config_loader.get_scrapy_settings()
    
    # Apply scrapy settings from config
    for key, value in scrapy_settings.items():
        base_settings.set(key, value)
    
    return CrawlerProcess(base_settings)

def main():
    print("🚀 Gazette Tracker - Starting up...")
    
    # Load configuration first
    try:
        config_loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create CLI parser with config defaults
    parser = create_cli_parser(config_loader)
    args = parser.parse_args()
    
    # Load configuration from specified file if different
    if args.config != "config.yaml":
        try:
            config_loader = ConfigLoader(args.config)
        except Exception as e:
            print(f"❌ Failed to load configuration from {args.config}: {e}")
            sys.exit(1)
    
    # Validate configuration
    config_errors = config_loader.validate_config()
    if config_errors:
        print("❌ Configuration validation errors:")
        for error in config_errors:
            print(f"   • {error}")
        sys.exit(1)
    
    # Show configuration and exit if requested
    if args.show_config:
        config_loader.print_config_summary()
        return
    
    # Configure logging
    configure_scrapy_logging(config_loader, args.c_logs)
    
    # Handle --update-years flag (only update JSON and exit)
    if args.update_years:
        year_data = update_years_json(config_loader)
        if year_data:
            print("💡 You can now run the downloader without --update-years flag.")
        else:
            print("\n❌ Failed to update years.json")
            sys.exit(1)
        return
    
    # Validate date inputs
    args.month, args.day = validate_date_inputs(args.month, args.day)
    
    # Handle years data for download operations
    year_data = None
    years_config = config_loader.get_spider_config('gazette_years')
    years_filename = years_config.get('output', {}).get('filename', 'years.json')
    
    if not os.path.exists(years_filename):
        print(f"\n📥 {years_filename} not found. Creating by fetching data from website...")
        year_data = update_years_json(config_loader)
    else:
        year_data = load_year_data(config_loader)
        if not year_data:
            print(f"\n📥 {years_filename} appears to be empty or invalid. Fetching fresh data...")
            year_data = update_years_json(config_loader)
    
    # Final check
    if not year_data:
        print(f"\n❌ Failed to load or fetch year data. Cannot proceed.")
        print("💡 Try using --update-years to fetch fresh data from the website.")
        sys.exit(1)
    
    # Create download process with config
    process = create_download_process(config_loader)
    
    # Get download spider config
    download_config = config_loader.get_spider_config('gazette_download')
    
    # Spider class that accepts config
    class ConfigurableGazetteDownloadSpider(GazetteDownloadSpider):
        def __init__(self, config=None, *args, **kwargs):
            self.spider_config = config or {}
            super().__init__(*args, **kwargs)
        
        def get_config_value(self, key_path, default=None):
            """Get nested configuration value using dot notation"""
            keys = key_path.split('.')
            value = self.spider_config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
    
    # Exact date mode (year + month + day)
    if args.year.lower() != "all" and args.month and args.day:
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
            sys.exit(1)
        
        # Check if data is available for this specific date
        if not check_data_availability(config_loader, args.year, year_entry["link"], args.month, args.day, args.lang):
            print(f"\n❌ No gazettes found for {args.year}-{args.month}-{args.day}.")
            print("💡 Try checking available dates or use a different date combination.")
            sys.exit(1)
        
        print(f"\n📅 Starting download for {args.year}-{args.month}-{args.day}...")
        process.crawl(
            ConfigurableGazetteDownloadSpider,
            config=download_config,
            year=args.year,
            year_url=year_entry["link"],
            lang=args.lang,
            month=args.month,
            day=args.day
        )
    
    # Year + Month mode
    elif args.year.lower() != "all" and args.month and not args.day:
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
            sys.exit(1)
        
        # Check if data is available for this month
        if not check_data_availability(config_loader, args.year, year_entry["link"], args.month, None, args.lang):
            # Optional: Show available dates for better user experience
            available_dates = get_available_dates(config_loader, args.year, year_entry["link"], args.lang)
            if available_dates:
                print("📅 Available dates in this year:")
                for date in available_dates[:10]:  # Show first 10 dates
                    print(f"   • {date.strftime('%Y-%m-%d')}")
                if len(available_dates) > 10:
                    print(f"   ... and {len(available_dates) - 10} more")
                    print(f"\n❌ No gazettes found for {args.year}-{args.month}.")
                    print("💡 Try checking available months or use a different month.")
                    sys.exit(1)
        
        print(f"\n📅 Starting download for {args.year}-{args.month} (entire month)...")
        process.crawl(
            ConfigurableGazetteDownloadSpider,
            config=download_config,
            year=args.year,
            year_url=year_entry["link"],
            lang=args.lang,
            month=args.month
        )
    
    # Year-only mode
    elif args.year.lower() != "all":
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
            sys.exit(1)
        
        # Check if data is available for this year
        if not check_data_availability(config_loader, args.year, year_entry["link"], None, None, args.lang):
            print(f"\n❌ No gazettes found for year {args.year}.")
            print("💡 Try checking available years or use a different year.")
            sys.exit(1)
        
        print(f"\n🔄 Starting download for year {args.year}...")
        process.crawl(
            ConfigurableGazetteDownloadSpider,
            config=download_config,
            year=args.year,
            year_url=year_entry["link"],
            lang=args.lang
        )
    
    # All-years mode
    else:
        if args.month or args.day:
            print(f"\n❌ Cannot use month/day filters with --year all. Please specify a specific year.")
            sys.exit(1)
        
        print(f"\n🔄 Starting download for all available years...")
        for entry in year_data:
            print(f"\n🔄 Processing year {entry['year']}...")
            process.crawl(
                ConfigurableGazetteDownloadSpider,
                config=download_config,
                year=entry["year"],
                year_url=entry["link"],
                lang=args.lang
            )
    
    try:
        process.start()
    except KeyboardInterrupt:
        print(f"\n🛑 Download interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()