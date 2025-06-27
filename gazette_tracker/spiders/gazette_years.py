import scrapy
import json
import os


class GazetteYearsSpider(scrapy.Spider):
    name = "gazette_years"
    start_urls = ["https://documents.gov.lk/view/extra-gazettes/egz.html"]

    def __init__(self, save_to_file=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected_years = []
        self.save_to_file = save_to_file

    def parse(self, response):
        """Parse the gazette years page and extract year links"""
        # Select all <a> tags inside the div with class 'button-container'
        links = response.css("div.button-container a.btn-primary")
        
        self.logger.info(f"Found {len(links)} year links on the page")
        
        for link in links:
            year_text = link.css("::text").get().strip()
            href = link.attrib['href']
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
                # Sort years in descending order (newest first)
                sorted_years = sorted(self.collected_years, 
                                    key=lambda x: x['year'], reverse=True)
                
                # Always save to years.json (create if doesn't exist)
                with open("years.json", "w", encoding="utf-8") as f:
                    json.dump(sorted_years, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Saved {len(sorted_years)} years to years.json")
                print(f"\n💾 Saved {len(sorted_years)} years to years.json")
                
            except Exception as e:
                self.logger.error(f"Error saving years to JSON file: {e}")
                print(f"\n❌ Error saving years to JSON file: {e}")
                
        elif self.save_to_file and not self.collected_years:
            self.logger.warning("No years data collected to save")
            print("\n⚠️ No years data collected to save")
            
            # Create empty years.json if no data collected
            try:
                with open("years.json", "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
                self.logger.info("Created empty years.json file")
                print("\n📝 Created empty years.json file")
            except Exception as e:
                self.logger.error(f"Could not create empty years.json: {e}")
                print(f"\n❌ Could not create empty years.json: {e}")
        
        self.logger.info(f"Total years collected: {len(self.collected_years)}")