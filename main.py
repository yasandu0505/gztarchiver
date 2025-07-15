from pathlib import Path
import yaml
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from document_scraper.document_scraper.spiders.years_spider import YearsSpider

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Get the project root
project_root = Path(__file__).parent

# Set the years.json storage location
output_path = project_root / config["output"]["years_json"]

# Ensure the parent directory exists
output_path.parent.mkdir(parents=True, exist_ok=True)

# Start crawler
process = CrawlerProcess(get_project_settings())
process.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
process.start()
