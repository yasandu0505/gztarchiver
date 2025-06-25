import json
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_download import GazetteDownloadSpider
from scrapy.utils.log import configure_logging
import logging

# CLI arguments
parser = argparse.ArgumentParser(description="Download gazettes by year and language.")
parser.add_argument("--year", default="all", help="Year to download (e.g., 2023 or 'all'). Default is 'all'.")
parser.add_argument("--lang", default="all", help="Language: en (English), si (Sinhala), ta (Tamil), or all. Default is 'all'.")
parser.add_argument("--c_logs", default="N", help="Enable Scrapy logs (Y/N). Default is N.")
args = parser.parse_args()

if args.c_logs.upper() != "Y":
    configure_logging({
        'LOG_LEVEL': 'CRITICAL',  # Hide everything below CRITICAL
        'LOG_FORMAT': '%(levelname)s: %(message)s',
        'LOG_STDOUT': False
    })
    logging.getLogger('scrapy').propagate = False  # Disable Scrapy's internal log propagation


# Load year->link mapping from JSON
with open("years.json", "r", encoding="utf-8") as f:
    year_data = json.load(f)
    
process = CrawlerProcess(get_project_settings())

# If year is "all", process every year
if args.year.lower() == "all":
    for entry in year_data:
        print(f"\n🔄 Starting download for year {entry['year']}...")
        process.crawl(GazetteDownloadSpider, year=entry["year"], year_url=entry["link"], lang=args.lang)
else:
    # Otherwise, find the matching year
    year_entry = next((item for item in year_data if item["year"] == args.year), None)
    if not year_entry:
        print(f"\n❌ Year '{args.year}' not found in years.json.")
        exit(1)
    print(f"\n🔄 Starting download for year {args.year}...")
    process.crawl(GazetteDownloadSpider, year=args.year, year_url=year_entry["link"], lang=args.lang)

process.start()
