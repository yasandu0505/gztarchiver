import os
import scrapy
from urllib.parse import urljoin
from pathlib import Path
import json
from datetime import datetime

class GazetteDownloadSpider(scrapy.Spider):
    name = "gazette_download"
    start_urls = []

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "LOG_LEVEL": "INFO",  # Hide DEBUG logs
        "LOG_FORMAT": "%(levelname)s: %(message)s",  # Cleaner log output
        "LOG_STDOUT": True,  # Capture print statements if used
    }
    
    def __init__(self, year=None, year_url=None, lang="all", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.lang_map = {
            "english": "en",
            "sinhala": "si",
            "tamil": "ta"
        }
        
        self.year = year
        self.lang = lang.lower()
        
        with open("years.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            year_entry = next((item for item in data if item["year"] == year), None)

        if year_entry:
            self.start_urls = [year_entry["link"]]
        else:
            raise ValueError(f"Year '{year}' not found in years.json.")
        
        self.base_dir = str(Path.home() / "Desktop/gazette-archive")

    def parse_date(self, date_str):
        """Parse date string and return year, month, day components"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.year, date_obj.month, date_obj.day
        except ValueError:
            try:
                # Try alternative format like DD/MM/YYYY
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                return date_obj.year, date_obj.month, date_obj.day
            except ValueError:
                try:
                    # Try another format like DD-MM-YYYY
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    return date_obj.year, date_obj.month, date_obj.day
                except ValueError:
                    # If all parsing fails, use current date components as fallback
                    self.logger.warning(f"Could not parse date: {date_str}, using current date")
                    now = datetime.now()
                    return now.year, now.month, now.day

    def parse(self, response):
        
        rows = response.css("table tbody tr")

        for row in rows:
            gazette_id = row.css("td:nth-child(1)::text").get(default="").strip().replace("/", "-")
            date = row.css("td:nth-child(2)::text").get(default="").strip()
            desc = row.css("td:nth-child(3)::text").get(default="").strip()

            # Parse the date to get year, month, day
            year, month, day = self.parse_date(date)
            
            # Create the new directory structure: year -> month -> date -> gazette_id
            year_folder = os.path.join(self.base_dir, str(year))
            month_folder = os.path.join(year_folder, f"{month:02d}")  # Zero-padded month
            date_folder = os.path.join(month_folder, f"{day:02d}")    # Zero-padded day
            gazette_folder = os.path.join(date_folder, gazette_id)
            
            # Create all directories in the hierarchy
            os.makedirs(gazette_folder, exist_ok=True)

            # Check if there are any <a> tags in the 4th <td>
            download_cell = row.css("td:nth-child(4)")
            pdf_buttons = download_cell.css("a")

            if not pdf_buttons:
                self.logger.info(f"[EMPTY] {date} {gazette_id} – No download links, only created folder. \n")
                continue

            for btn in pdf_buttons:
                
                full_lang_text = btn.css("button::text").get(default="unknown").strip().lower()
                short_code = self.lang_map.get(full_lang_text)
                
                if not short_code:
                    self.logger.warning(f"[UNKNOWN LANGUAGE] {full_lang_text} – Skipping.")
                    continue
                
                if self.lang != "all" and self.lang != short_code:
                    continue  # skip other languages

                pdf_url = urljoin(response.url, btn.attrib["href"])
                file_path = os.path.join(gazette_folder, f"{gazette_id}_{full_lang_text}.pdf")

                yield scrapy.Request(
                    url=pdf_url,
                    callback=self.save_pdf,
                    meta={
                        "file_path": file_path,
                        "gazette_id": gazette_id,
                        "lang": full_lang_text,
                        "date": date
                    },
                    errback=self.download_failed,
                    dont_filter=True
                )

    def save_pdf(self, response):
        path = response.meta["file_path"]
        with open(path, "wb") as f:
            f.write(response.body)
        self.logger.info(f"[SAVED] Gazette {response.meta['date']} {response.meta['gazette_id']} ({response.meta['lang']}) \n")

    def download_failed(self, failure):
        request = failure.request
        gazette_id = request.meta.get("gazette_id", "unknown")
        lang = request.meta.get("lang", "unknown")
        self.logger.warning(f"[FAILED] {gazette_id} ({lang}) – {request.url}")
        with open("failed_downloads.log", "a") as log_file:
            log_file.write(f"{request.url},{gazette_id},{lang}\n")