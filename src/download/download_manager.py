"""
Download Manager Module
Handles gazette download operations and data availability checks.
"""

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_download import GazetteDownloadSpider
from src.utils.data_checker import DataAvailabilityChecker


class DownloadManager:
    """Manages gazette download operations."""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.download_config = config_loader.get_spider_config('gazette_download')
        self.data_checker = DataAvailabilityChecker(config_loader)
        self.process = self._create_download_process()
    
    def _create_download_process(self):
        """Create CrawlerProcess with settings from config."""
        base_settings = get_project_settings()
        scrapy_settings = self.config_loader.get_scrapy_settings()
        
        # Apply scrapy settings from config
        for key, value in scrapy_settings.items():
            base_settings.set(key, value)
        
        return CrawlerProcess(base_settings)
    
    def check_data_availability(self, year, year_url, month=None, day=None, lang='all'):
        """Check if gazettes are available for the specified criteria."""
        return self.data_checker.check_data_availability(year, year_url, month, day, lang)
    
    def get_available_dates(self, year, year_url, lang='all'):
        """Get all available dates for a given year."""
        return self.data_checker.get_available_dates(year, year_url, lang)
    
    def download_all_years(self, year_data, lang):
        """Download gazettes for all available years."""
        for entry in year_data:
            print(f"\n🔄 Processing year {entry['year']}...")
            self.process.crawl(
                self._get_configurable_spider(),
                config=self.download_config,
                year=entry["year"],
                year_url=entry["link"],
                lang=lang
            )
        
        self.process.start()
    
    def download_year(self, year, year_url, lang):
        """Download gazettes for a specific year."""
        self.process.crawl(
            self._get_configurable_spider(),
            config=self.download_config,
            year=year,
            year_url=year_url,
            lang=lang
        )
        self.process.start()
    
    def download_month(self, year, year_url, lang, month):
        """Download gazettes for a specific month."""
        self.process.crawl(
            self._get_configurable_spider(),
            config=self.download_config,
            year=year,
            year_url=year_url,
            lang=lang,
            month=month
        )
        self.process.start()
    
    def download_specific_date(self, year, year_url, lang, month, day):
        """Download gazettes for a specific date."""
        self.process.crawl(
            self._get_configurable_spider(),
            config=self.download_config,
            year=year,
            year_url=year_url,
            lang=lang,
            month=month,
            day=day
        )
        self.process.start()
    
    def _get_configurable_spider(self):
        """Get the configurable spider class."""
        class ConfigurableGazetteDownloadSpider(GazetteDownloadSpider):
            """Spider class that accepts config."""
            
            def __init__(self, config=None, *args, **kwargs):
                self.spider_config = config or {}
                super().__init__(*args, **kwargs)
            
            def get_config_value(self, key_path, default=None):
                """Get nested configuration value using dot notation."""
                keys = key_path.split('.')
                value = self.spider_config
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return default
                return value
        
        return ConfigurableGazetteDownloadSpider