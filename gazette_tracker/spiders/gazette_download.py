import os
import scrapy
from urllib.parse import urljoin
from pathlib import Path


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
        self.year = year
        self.lang = lang.lower()
        if year_url:
            self.start_urls = [year_url]
        self.base_dir = str(Path.home() / "Desktop/gazette-archive")

    def parse(self, response):
        rows = response.css("table tbody tr")

        for row in rows:
            gazette_id = row.css("td:nth-child(1)::text").get(default="").strip().replace("/", "-")
            date = row.css("td:nth-child(2)::text").get(default="").strip()
            desc = row.css("td:nth-child(3)::text").get(default="").strip()

            # Directory setup
            year_folder = os.path.join(self.base_dir, self.year)
            folder_name = f"{date}_{gazette_id}"
            gazette_folder = os.path.join(year_folder, folder_name)
            os.makedirs(gazette_folder, exist_ok=True)

            # Check if there are any <a> tags in the 4th <td>
            download_cell = row.css("td:nth-child(4)")
            pdf_buttons = download_cell.css("a")

            if not pdf_buttons:
                self.logger.info(f"[EMPTY] {gazette_id} – No download links, only created folder. \n")
                continue

            for btn in pdf_buttons:
                lang_text = btn.css("button::text").get(default="unknown").strip().lower()
                if self.lang != "all" and self.lang != lang_text:
                    continue  # skip other languages

                pdf_url = urljoin(response.url, btn.attrib["href"])
                file_path = os.path.join(gazette_folder, f"{gazette_id}_{lang_text}.pdf")

                yield scrapy.Request(
                    url=pdf_url,
                    callback=self.save_pdf,
                    meta={
                        "file_path": file_path,
                        "gazette_id": gazette_id,
                        "lang": lang_text
                    },
                    errback=self.download_failed,
                    dont_filter=True
                )

    def save_pdf(self, response):
        path = response.meta["file_path"]
        with open(path, "wb") as f:
            f.write(response.body)
        self.logger.info(f"[SAVED] Gazette {response.meta['gazette_id']} ({response.meta['lang']}) \n")

    def download_failed(self, failure):
        request = failure.request
        gazette_id = request.meta.get("gazette_id", "unknown")
        lang = request.meta.get("lang", "unknown")
        self.logger.warning(f"[FAILED] {gazette_id} ({lang}) – {request.url}")
        with open("failed_downloads.log", "a") as log_file:
            log_file.write(f"{request.url},{gazette_id},{lang}\n")
