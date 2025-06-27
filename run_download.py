import json
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_download import GazetteDownloadSpider
from gazette_tracker.spiders.gazette_years import GazetteYearsSpider  # Import the years spider
from scrapy.utils.log import configure_logging
import logging
import sys
import os

# CLI arguments
parser = argparse.ArgumentParser(description="Download gazettes by year and language.")
parser.add_argument("--year", default="all", help="Year to download (e.g., 2023 or 'all'). Default is 'all'.")
parser.add_argument("--month", help="Month to download (e.g., 01, 12). Optional.")
parser.add_argument("--day", help="Day to download (e.g., 01, 31). Optional.")
parser.add_argument("--lang", default="all", help="Language: en (English), si (Sinhala), ta (Tamil), or all. Default is 'all'.")
parser.add_argument("--c_logs", default="N", help="Enable Scrapy logs (Y/N). Default is N.")
parser.add_argument("--update_years", action="store_true", help="Update years.json by scraping the website first.")
args = parser.parse_args()

# Configure logging
if args.c_logs.upper() != "Y":
    configure_logging({
        'LOG_LEVEL': 'CRITICAL',
        'LOG_FORMAT': '%(levelname)s: %(message)s',
        'LOG_STDOUT': False
    })
    logging.getLogger('scrapy').propagate = False

# Function to update years.json using GazetteYearsSpider
def update_years_json():
    """Update years.json by scraping the website using GazetteYearsSpider."""
    print("\n🔄 Fetching years data from website...")
    
    # Create a separate process for the years spider
    years_settings = get_project_settings()
    years_settings.set('LOG_LEVEL', 'CRITICAL')
    years_settings.set('LOG_STDOUT', False)
    years_process = CrawlerProcess(years_settings)
    
    # Configure and start the GazetteYearsSpider
    years_process.crawl(GazetteYearsSpider, save_to_file=True)
    years_process.start()  # This will block until spider finishes
    
    # Check if years.json was created/updated
    if os.path.exists("years.json"):
        try:
            with open("years.json", "r", encoding="utf-8") as f:
                year_data = json.load(f)
            if year_data:
                print(f"✅ Successfully updated years.json with {len(year_data)} years")
                return year_data
            else:
                print("⚠️ years.json was created but is empty")
                return None
        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON format in years.json")
            return None
    else:
        print("❌ Failed to create years.json")
        return None

# Function to load year data
def load_year_data():
    """Load year data from years.json or return None if not found."""
    try:
        with open("years.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print("\n❌ Error: Invalid JSON format in years.json.")
        sys.exit(1)

# Helper: fetch year entry from year data
def get_year_entry(year_data, year):
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

# Main execution
def main():
    # Handle --update-years flag (only update JSON and exit)
    if args.update_years:
        print("\n🔄 --update-years flag detected. Updating years.json...")
        year_data = update_years_json()
        if year_data:
            print(f"\n✅ years.json successfully updated with {len(year_data)} years.")
            print("💡 You can now run the downloader without --update-years flag.")
        else:
            print("\n❌ Failed to update years.json")
            sys.exit(1)
        return  # Exit after updating
    
    # Validate inputs for download operations
    validate_date_inputs()
    
    # Handle years data for download operations
    year_data = None
    
    if not os.path.exists("years.json"):
        print("\n📥 years.json not found. Creating by fetching data from website...")
        year_data = update_years_json()
    else:
        year_data = load_year_data()
        if not year_data:
            print("\n📥 years.json appears to be empty or invalid. Fetching fresh data...")
            year_data = update_years_json()
    
    # Final check
    if not year_data:
        print("\n❌ Failed to load or fetch year data. Cannot proceed.")
        print("💡 Try using --update-years to fetch fresh data from the website.")
        sys.exit(1)
    
    # Create process for download spiders
    download_settings = get_project_settings()
    process = CrawlerProcess(download_settings)

    # Exact date mode (year + month + day)
    if args.year.lower() != "all" and args.month and args.day:
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
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

    # Year + Month mode
    elif args.year.lower() != "all" and args.month and not args.day:
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
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
        year_entry = get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
            sys.exit(1)

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

if __name__ == "__main__":
    main()