import scrapy
from pathlib import Path
import csv

class PDFDownloaderSpider(scrapy.Spider):
    name = "pdf_downloader"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS": 2,
        "RETRY_ENABLED": True,
        "LOG_LEVEL": "INFO"
    }

    def __init__(self, download_metadata=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.download_metadata = download_metadata or []

    def start_requests(self):
        for item in self.download_metadata:
            url = item.get("download_url")
            if not url or url == "N/A":
                # Create folder structure
                folder_path = item["file_path"].parent
                folder_path.mkdir(parents=True, exist_ok=True)
                
                # Log to unavailable.csv
                self.log_status(item, "unavailable")
                self.logger.info(f"⚠️ Logged as unavailable: {item['doc_id']}")
                # Continue to next item instead of yielding a request
                continue
            
            # Only yield request for valid URLs
            yield scrapy.Request(
                url=url,
                callback=self.save_pdf,
                errback=self.handle_failure,
                meta={"item": item},
                dont_filter=True
            )

    def save_pdf(self, response):
        item = response.meta["item"]
        file_path = item["file_path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "wb") as f:
                f.write(response.body)
            self.log_status(item, "archived")
            self.logger.info(f"✅ Downloaded: {file_path}")
        except Exception as e:
            self.log_status(item, "failed")
            self.logger.error(f"❌ Failed to save {file_path}: {e}")

    def handle_failure(self, failure):
        item = failure.request.meta["item"]
        self.log_status(item, "failed")
        self.logger.error(f"❌ Request failed: {item['download_url']}")

    def log_status(self, item, status):
        try:
            year = item["file_path"].parts[-5]  # Extract year from the path
            base_log_dir = Path(item["file_path"]).parents[4] / year
            base_log_dir.mkdir(parents=True, exist_ok=True)

            log_file = base_log_dir / f"{status}.csv"
            file_exists = log_file.exists()

            with open(log_file, "a", newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    writer.writerow(["doc_id", "download_url", "file_path"])
                
                writer.writerow([item["doc_id"], item["download_url"], str(item["file_path"])])
        except Exception as e:
            self.logger.error(f"❌ Failed to log status for {item.get('doc_id', 'unknown')}: {e}")