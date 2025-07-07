"""
Years Data Manager Module
Handles loading, updating, and managing years.json data.
"""

import json
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from gazette_tracker.spiders.gazette_years import GazetteYearsSpider


class YearsManager:
    """Manages years data from years.json file."""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.years_config = config_loader.get_spider_config('gazette_years')
        self.filename = self.years_config.get('output', {}).get('filename', 'years.json')
    
    def get_or_fetch_years_data(self):
        """Get years data from file or fetch from website if not available."""
        if not os.path.exists(self.filename):
            print(f"\n📥 {self.filename} not found. Creating by fetching data from website...")
            return self.update_years_json()
        
        year_data = self.load_year_data()
        if not year_data:
            print(f"\n📥 {self.filename} appears to be empty or invalid. Fetching fresh data...")
            return self.update_years_json()
        
        return year_data
    
    def load_year_data(self):
        """Load year data from years.json file."""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(f"\n❌ Error: Invalid JSON format in {self.filename}.")
            sys.exit(1)
    
    def update_years_json(self):
        """Update years.json using GazetteYearsSpider."""
        print("\n🔄 Fetching years data from website...")
        
        # Create process settings
        scrapy_settings = self.config_loader.get_scrapy_settings()
        years_settings = get_project_settings()
        
        # Apply scrapy settings from config
        for key, value in scrapy_settings.items():
            years_settings.set(key, value)
        
        years_process = CrawlerProcess(years_settings)
        
        # Get output settings from config
        output_config = self.years_config.get('output', {})
        save_to_file = output_config.get('save_to_file', True)
        
        # Configure and start the GazetteYearsSpider
        years_process.crawl(
            GazetteYearsSpider, 
            config=self.years_config,
            save_to_file=save_to_file
        )
        years_process.start()
        
        # Validate the created file
        return self._validate_years_file()
    
    def _validate_years_file(self):
        """Validate the years.json file after creation."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    year_data = json.load(f)
                if year_data:
                    print(f"✅ Successfully updated {self.filename} with {len(year_data)} years")
                    return year_data
                else:
                    print(f"⚠️ {self.filename} was created but is empty")
                    return None
            except json.JSONDecodeError:
                print(f"❌ Error: Invalid JSON format in {self.filename}")
                return None
        else:
            print(f"❌ Failed to create {self.filename}")
            return None