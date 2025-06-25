import scrapy

class GazetteYearsSpider(scrapy.Spider):
    name = "gazette_years"
    start_urls = ["https://documents.gov.lk/view/extra-gazettes/egz.html"]

    def parse(self, response):
        # Select all <a> tags inside the div with class 'button-container'
        links = response.css("div.button-container a.btn-primary")
        
        for link in links:
            year_text = link.css("::text").get().strip()
            href = link.attrib['href']
            full_url = response.urljoin(href)
            
            yield {
                'year': year_text,
                'link': full_url
            }
