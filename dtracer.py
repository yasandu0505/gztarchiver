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
        log_level = scrapy_settings.get('LOG_LEVEL', 'CRITICAL')
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
    by performing a quick scrape to see if any data exists.
    Returns True if data is available, False otherwise.
    """
    print(f"🔍 Checking data availability for {year}" + 
          (f"-{month}" if month else "") + 
          (f"-{day}" if day else "") + "...")
    
    try:
        import scrapy
        from scrapy.http import Request
        
        # Create a minimal spider just for validation
        class QuietValidationSpider(scrapy.Spider):
            name = 'validation_spider'
            
            def __init__(self, config=None, year=None, year_url=None, lang='all', month=None, day=None, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.spider_config = config or {}
                self.year = year
                self.year_url = year_url
                self.lang = lang
                self.month = month
                self.day = day
                self.found_gazettes = False
                self.custom_settings = {
                    'LOG_LEVEL': 'CRITICAL',  # Suppress all logs
                    'DOWNLOAD_DELAY': 0,
                    'ROBOTSTXT_OBEY': False,
                    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            
            def start_requests(self):
                """Start with the year URL"""
                yield Request(
                    url=self.year_url,
                    callback=self.parse_year_page,
                    dont_filter=True
                )
            
            def parse_year_page(self, response):
                """Parse year page to find month links"""
                if self.month:
                    # Look for specific month - avoid PDF links
                    month_links = response.css(f"a[href*='{self.month}']:not([href$='.pdf'])::attr(href)").getall()
                    if month_links:
                        month_url = response.urljoin(month_links[0])
                        yield Request(
                            url=month_url,
                            callback=self.parse_month_page,
                            dont_filter=True
                        )
                    else:
                        # Month not found, stop here
                        self.crawler.engine.close_spider(self, 'month_not_found')
                else:
                    # Check any month for general availability - avoid PDF links
                    month_links = response.css("a[href*='/']:not([href$='.pdf'])::attr(href)").getall()
                    if month_links:
                        # Just check the first month found
                        month_url = response.urljoin(month_links[0])
                        yield Request(
                            url=month_url,
                            callback=self.parse_month_page,
                            dont_filter=True
                        )
            
            def parse_month_page(self, response):
                """Parse month page to check for gazettes"""
                if self.day:
                    # Look for specific day - avoid PDF links
                    day_links = response.css(f"a[href*='{self.day}']:not([href$='.pdf'])::attr(href)").getall()
                    if day_links:
                        day_url = response.urljoin(day_links[0])
                        yield Request(
                            url=day_url,
                            callback=self.check_gazette_page,
                            dont_filter=True
                        )
                    else:
                        # Day not found
                        self.crawler.engine.close_spider(self, 'day_not_found')
                else:
                    # Check current page for gazettes
                    yield Request(
                        url=response.url,
                        callback=self.check_gazette_page,
                        dont_filter=True
                    )
            
            def check_gazette_page(self, response):
                """Check if this page has any gazette PDFs"""
                # Check if we accidentally landed on a PDF file
                content_type = response.headers.get('content-type', b'').decode('utf-8').lower()
                if 'application/pdf' in content_type or response.url.endswith('.pdf'):
                    # If we're on a PDF page, that means PDFs exist
                    self.found_gazettes = True
                    self.crawler.engine.close_spider(self, 'validation_complete')
                    return
                
                try:
                    # Look for PDF links only if this is an HTML page
                    pdf_links = response.css("a[href$='.pdf'], a[href*='.pdf']").getall()
                    
                    if pdf_links:
                        # Apply language filter if specified
                        if self.lang != 'all':
                            # Check if any PDFs match the language filter
                            lang_patterns = {
                                'en': ['english', 'en'],
                                'si': ['sinhala', 'si', 'sinh'],
                                'ta': ['tamil', 'ta', 'tam']
                            }
                            patterns = lang_patterns.get(self.lang.lower(), [])
                            
                            found_matching = False
                            for link in pdf_links:
                                link_text = link.lower()
                                if any(pattern in link_text for pattern in patterns):
                                    found_matching = True
                                    break
                            
                            if found_matching:
                                self.found_gazettes = True
                        else:
                            # No language filter, any PDF counts
                            self.found_gazettes = True
                
                except Exception as e:
                    # If CSS parsing fails, assume no gazettes found
                    pass
                
                # Close spider after checking
                self.crawler.engine.close_spider(self, 'validation_complete')
        
        # Create a silent crawler process
        temp_settings = get_project_settings()
        temp_settings.set('LOG_LEVEL', 'CRITICAL')
        temp_settings.set('LOG_ENABLED', False)
        temp_settings.set('DOWNLOAD_DELAY', 0)
        temp_settings.set('ROBOTSTXT_OBEY', False)
        
        temp_process = CrawlerProcess(temp_settings)
        
        # Run the validation spider
        deferred = temp_process.crawl(
            QuietValidationSpider,
            config=config_loader.get_spider_config('gazette_download'),
            year=year,
            year_url=year_url,
            lang=lang,
            month=month,
            day=day
        )
        
        temp_process.start()
        
        # Check if any gazettes were found
        spider_instance = None
        for crawler in temp_process.crawlers:
            if hasattr(crawler.spider, 'found_gazettes'):
                spider_instance = crawler.spider
                break
        
        return spider_instance.found_gazettes if spider_instance else False
        
    except Exception as e:
        print(f"⚠️ Warning: Could not validate data availability: {e}")
        # If validation fails, proceed anyway (fail gracefully)
        return True

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
        
        print('hi2')
        # Check if data is available for this month
        if not check_data_availability(config_loader, args.year, year_entry["link"], args.month, None, args.lang):
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
            print(f"\n❌ No gazettes found for {args.year}")
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