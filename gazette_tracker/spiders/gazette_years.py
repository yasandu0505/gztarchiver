import scrapy
import json

class GazetteYearsSpider(scrapy.Spider):
    name = "gazette_years"
    
    def __init__(
        self, 
        save_to_file=True, 
        config=None,  # Expect a dict to be passed instead of YAML filename
        *args, 
        **kwargs):
        super().__init__(*args, **kwargs)
        self.collected_years = []
        self.save_to_file = save_to_file
        self.config = config or {}  # Default to empty dict if not provided

        # Set spider configuration from the provided config dict
        spider_config = self.config.get('gazette_years_spider', {})
        
        # Set start_urls from config or default
        self.start_urls = spider_config.get('start_urls', [
            "https://documents.gov.lk/view/extra-gazettes/egz.html"
        ])
        
        # Store selectors from config
        self.selectors = spider_config.get('selectors', {})
        
        # Store output settings from config
        self.output_config = spider_config.get('output', {})
        
        # Override save_to_file from config if not explicitly passed
        if 'save_to_file' not in kwargs:
            self.save_to_file = self.output_config.get('save_to_file', True)

    def parse(self, response):
        """Parse the gazette years page and extract year links"""
        # Use selectors from config, with fallbacks to original selectors
        year_links_selector = self.selectors.get('year_links', "div.button-container a.btn-primary")
        year_text_selector = self.selectors.get('year_text', "::text")
        
        links = response.css(year_links_selector)
        self.logger.info(f"Found {len(links)} year links on the page")
        
        for link in links:
            year_text = link.css(year_text_selector).get()
            if year_text:
                year_text = year_text.strip()
            else:
                continue
            href = link.attrib.get('href')
            if not href:
                continue
            full_url = response.urljoin(href)
            year_data = {
                'year': year_text,
                'link': full_url
            }
            self.collected_years.append(year_data)
            self.logger.info(f"Collected year: {year_text} -> {full_url}")
            yield year_data
    
    def closed(self, reason):
        """Called when the spider is closed - save data to JSON file"""
        self.logger.info(f"Spider closed with reason: {reason}")
        if self.save_to_file and self.collected_years:
            try:
                filename = self.output_config.get('filename', 'years.json')
                sort_descending = self.output_config.get('sort_descending', True)
                encoding = self.output_config.get('encoding', 'utf-8')
                indent = self.output_config.get('indent', 2)
                # Sort years based on config setting
                sorted_years = sorted(self.collected_years, 
                                     key=lambda x: x['year'], 
                                     reverse=sort_descending)
                with open(filename, "w", encoding=encoding) as f:
                    json.dump(sorted_years, f, indent=indent, ensure_ascii=False)
                self.logger.info(f"Saved {len(sorted_years)} years to {filename}")
                print(f"\n💾 Saved {len(sorted_years)} years to {filename}")
            except Exception as e:
                self.logger.error(f"Error saving years to JSON file: {e}")
                print(f"\n❌ Error saving years to JSON file: {e}")
        elif self.save_to_file and not self.collected_years:
            self.logger.warning("No years data collected to save")
            print("\n⚠️ No years data collected to save")
            try:
                filename = self.output_config.get('filename', 'years.json')
                encoding = self.output_config.get('encoding', 'utf-8')
                indent = self.output_config.get('indent', 2)
                with open(filename, "w", encoding=encoding) as f:
                    json.dump([], f, indent=indent, ensure_ascii=False)
                self.logger.info(f"Created empty {filename} file")
                print(f"\n📝 Created empty {filename} file")
            except Exception as e:
                self.logger.error(f"Could not create empty {filename}: {e}")
                print(f"\n❌ Could not create empty {filename}: {e}")        
        self.logger.info(f"Total years collected: {len(self.collected_years)}")