import scrapy
from urllib.parse import urljoin

class DocMetadataSpider(scrapy.Spider):
    name = "doc_metadata_spider"

    def __init__(self, url=None, lang=None, **kwargs):
        self.start_urls = [url]
        self.lang = lang.lower()
        super().__init__(**kwargs)

    def parse(self, response):
        lang_map = {
            "en": ("English", "btn-primary"),
            "si": ("Sinhala", "btn-secondary"),
            "ta": ("Tamil", "btn-success")
        }

        lang_label, lang_class = lang_map.get(self.lang, ("English", "btn-primary"))

        rows = response.css("table.table-bordered tbody tr")
        print("\n--- Gazette Metadata ---\n")
        for row in rows:
            gazette_number = row.css("td:nth-child(1)::text").get().strip()
            gazette_date = row.css("td:nth-child(2)::text").get().strip()
            description = row.css("td:nth-child(3)::text").get().strip()
            
            doc_id = gazette_number.replace('/', '-')
            availability = "Unavailable"
            download_url = "N/A"

            download_td = row.css("td:nth-child(4)")
            lang_button = download_td.css(f"a:has(button.{lang_class})")

            if lang_button:
                href = lang_button.css("::attr(href)").get()
                if href:
                    download_url = urljoin(response.url, href)
                    availability = "Available"

            print(f"📄 Gazette ID: {doc_id}")
            print(f"📅 Date      : {gazette_date}")
            print(f"📝 Description: {description}")
            print(f"🌐 Link ({lang_label}): {download_url}")
            print(f"✅ Available : {availability}")
            print("-" * 50)
