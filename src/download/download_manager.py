from document_scraper.document_scraper.spiders import PDFDownloaderSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def download_docs(download_metadata):
    process = CrawlerProcess(get_project_settings())
    process.crawl(PDFDownloaderSpider, download_metadata=download_metadata)
    process.start()   
    
   