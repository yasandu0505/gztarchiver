from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from document_scraper.document_scraper import YearsSpider
import json
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