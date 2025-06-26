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
with open("years.json", "r", encoding="utf-8") as f:
    year_data = json.load(f)

process = CrawlerProcess(get_project_settings())

# Helper: fetch year entry from years.json
def get_year_entry(year):
    return next((item for item in year_data if item["year"] == year), None)

# Exact date mode (year + month + day)
if args.year.lower() != "all" and args.month and args.day:
    year_entry = get_year_entry(args.year)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
        sys.exit(1)

    print(f"\n📅 Starting download for {args.year}-{args.month}-{args.day}...")
    process.crawl(
        GazetteDownloadSpider,
        year=args.year,
        year_url=year_entry["link"],
        lang=args.lang,
        month=args.month,
        day=args.day
    )

# Year-only mode
elif args.year.lower() != "all":
    year_entry = get_year_entry(args.year)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
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
    for entry in year_data:
        print(f"\n🔄 Starting download for year {entry['year']}...")
        process.crawl(
            GazetteDownloadSpider,
            year=entry["year"],
            year_url=entry["link"],
            lang=args.lang
        )

process.start()
