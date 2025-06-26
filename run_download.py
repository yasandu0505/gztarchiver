import json
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_download import GazetteDownloadSpider
from scrapy.utils.log import configure_logging
import logging
import sys

# CLI arguments
parser = argparse.ArgumentParser(description="Download gazettes by year and language.")
parser.add_argument("--year", default="all", help="Year to download (e.g., 2023 or 'all'). Default is 'all'.")
parser.add_argument("--month", help="Month to download (e.g., 01, 12). Optional.")
parser.add_argument("--day", help="Day to download (e.g., 01, 31). Optional.")
parser.add_argument("--lang", default="all", help="Language: en (English), si (Sinhala), ta (Tamil), or all. Default is 'all'.")
parser.add_argument("--c_logs", default="N", help="Enable Scrapy logs (Y/N). Default is N.")
args = parser.parse_args()

# Configure logging
if args.c_logs.upper() != "Y":
    configure_logging({
        'LOG_LEVEL': 'CRITICAL',
        'LOG_FORMAT': '%(levelname)s: %(message)s',
        'LOG_STDOUT': False
    })
    logging.getLogger('scrapy').propagate = False

# Load year -> URL mapping
try:
    with open("years.json", "r", encoding="utf-8") as f:
        year_data = json.load(f)
except FileNotFoundError:
    print("\n❌ Error: years.json file not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print("\n❌ Error: Invalid JSON format in years.json.")
    sys.exit(1)

process = CrawlerProcess(get_project_settings())

# Helper: fetch year entry from years.json
def get_year_entry(year):
    return next((item for item in year_data if item["year"] == year), None)

# Validate month and day inputs
def validate_date_inputs():
    if args.month:
        try:
            month_int = int(args.month)
            if month_int < 1 or month_int > 12:
                print(f"\n❌ Invalid month '{args.month}'. Must be between 01-12.")
                sys.exit(1)
            # Ensure month is zero-padded
            args.month = f"{month_int:02d}"
        except ValueError:
            print(f"\n❌ Invalid month format '{args.month}'. Use format: 01, 02, ..., 12.")
            sys.exit(1)
    
    if args.day:
        try:
            day_int = int(args.day)
            if day_int < 1 or day_int > 31:
                print(f"\n❌ Invalid day '{args.day}'. Must be between 01-31.")
                sys.exit(1)
            # Ensure day is zero-padded
            args.day = f"{day_int:02d}"
        except ValueError:
            print(f"\n❌ Invalid day format '{args.day}'. Use format: 01, 02, ..., 31.")
            sys.exit(1)

# Custom spider class that checks if any gazettes were found
class GazetteDownloadSpiderWithValidation(GazetteDownloadSpider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.found_matching_gazettes = False
        
    def parse(self, response):
        # First, check if any gazettes match our filters
        rows = response.css("table tbody tr")
        matching_count = 0
        
        for row in rows:
            date = row.css("td:nth-child(2)::text").get(default="").strip()
            
            # Check if this gazette matches our date filter
            if self.matches_date_filter(date):
                matching_count += 1
                break  # We found at least one match
        
        if matching_count == 0:
            # No matching gazettes found
            filter_desc = []
            if self.month:
                filter_desc.append(f"month {self.month}")
            if self.day:
                filter_desc.append(f"day {self.day}")
            
            filter_text = " and ".join(filter_desc) if filter_desc else "specified filters"
            print(f"\n❌ No gazettes found for year {self.year} with {filter_text}")
            
            # Log the finding
            if hasattr(self, 'file_logger'):
                self.file_logger.info(f"No gazettes found matching filters - Year: {self.year}, Month: {self.month}, Day: {self.day}")
            
            return  # Stop processing
        
        # If we reach here, we found matching gazettes
        self.found_matching_gazettes = True
        
        # Continue with normal processing
        yield from super().parse(response)

# Validate inputs
validate_date_inputs()

# Exact date mode (year + month + day)
if args.year.lower() != "all" and args.month and args.day:
    year_entry = get_year_entry(args.year)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
        sys.exit(1)

    print(f"\n📅 Starting download for {args.year}-{args.month}-{args.day}...")
    process.crawl(
        GazetteDownloadSpiderWithValidation,
        year=args.year,
        year_url=year_entry["link"],
        lang=args.lang,
        month=args.month,
        day=args.day
    )

# Year + Month mode (NEW: handles month-only filtering)
elif args.year.lower() != "all" and args.month and not args.day:
    year_entry = get_year_entry(args.year)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
        sys.exit(1)

    print(f"\n📅 Starting download for {args.year}-{args.month} (entire month)...")
    process.crawl(
        GazetteDownloadSpiderWithValidation,
        year=args.year,
        year_url=year_entry["link"],
        lang=args.lang,
        month=args.month
    )

# Year-only mode
elif args.year.lower() != "all":
    year_entry = get_year_entry(args.year)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
        sys.exit(1)

    if args.month:
        print(f"\n📅 Starting download for {args.year}-{args.month} (entire month)...")
        process.crawl(
            GazetteDownloadSpiderWithValidation,
            year=args.year,
            year_url=year_entry["link"],
            lang=args.lang,
            month=args.month
        )
    else:
        print(f"\n🔄 Starting download for year {args.year}...")
        process.crawl(
            GazetteDownloadSpider,
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
            GazetteDownloadSpider,
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