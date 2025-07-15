from src.cmd import parse_args, identify_input_kind
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from document_scraper.document_scraper import YearsSpider
from pathlib import Path
import yaml
import json
import sys
import logging
from scrapy.utils.log import configure_logging

def scrape_years_metadata(url, output_path):
    # Suppress all Scrapy logs
    configure_logging(install_root_handler=False)
    logging.getLogger('scrapy').setLevel(logging.ERROR)
    
    # Setup crawler
    settings = get_project_settings()
    settings.set('LOG_LEVEL', 'ERROR')
    
    # Start crawler
    process = CrawlerProcess(settings=settings)
    process.crawl(YearsSpider, url=url, output_path=str(output_path))
    process.start()

def load_scraped_years(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return [entry["year"] for entry in json.load(f)]

def main():
    args = parse_args()
    kind = identify_input_kind(args)

    if kind == "invalid":
        print("Invalid input! --year and --lang are required at minimum.")
        sys.exit(1)

    # Project root
    project_root = Path(__file__).parent

    # Load config.yaml
    with open(project_root / "config.yaml") as f:
        config = yaml.safe_load(f)

    # Resolve years.json path
    output_path = project_root / config["output"]["years_json"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Scrape latest year links and save to years.json
    print("Checking for updates from the website...")
    scrape_years_metadata(config["scrape"]["url"], output_path)
    print(f"Updated year metadata saved to {output_path}")

    # Step 2: Validate CLI --year against scraped data
    scraped_years = load_scraped_years(output_path)
    if str(args.year) not in scraped_years:
        print(f"Error: Year '{args.year}' is not available in scraped data.")
        print(f"Available years: {', '.join(scraped_years)}")
        sys.exit(1)

    # Step 3: Continue processing with valid input
    print(f"✅ Year '{args.year}' is valid.")
    print(f"Input kind: {kind}")
    print(f"Parameters: year={args.year}, month={args.month}, day={args.day}, lang={args.lang}")

    # : Call the correct spider/downloader here based on input kind

if __name__ == "__main__":
    main()
