import os
import scrapy
from urllib.parse import urljoin
from pathlib import Path
import json
import csv
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
        
        # Setup logging files for this year
        self.year_folder = os.path.join(self.base_dir, str(year))
        os.makedirs(self.year_folder, exist_ok=True)
        
        self.archive_log_file = os.path.join(self.year_folder, f"{year}_archive_log.csv")
        self.failed_log_file = os.path.join(self.year_folder, f"{year}_failed_log.csv")
        
        # Load existing logs to track what's already been processed
        self.archived_files = self.load_archived_files()
        self.failed_files = self.load_failed_files()
        
        # Initialize log files if they don't exist
        self.initialize_log_files()

    def initialize_log_files(self):
        """Initialize CSV log files with headers if they don't exist"""
        # Archive log headers
        if not os.path.exists(self.archive_log_file):
            with open(self.archive_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'gazette_id', 'date', 'language', 'description', 'file_path', 'file_size_bytes', 'status'])
        
        # Failed log headers
        if not os.path.exists(self.failed_log_file):
            with open(self.failed_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'gazette_id', 'date', 'language', 'description','url', 'error_reason', 'retry_count'])

    def load_archived_files(self):
        """Load list of already archived files from CSV"""
        archived = set()
        if os.path.exists(self.archive_log_file):
            try:
                with open(self.archive_log_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['status'] == 'SUCCESS':
                            # Create unique identifier: gazette_id + language
                            file_key = f"{row['gazette_id']}_{row['language']}"
                            archived.add(file_key)
            except Exception as e:
                self.logger.warning(f"Could not load archive log: {e}")
        return archived

    def load_failed_files(self):
        """Load list of failed files from CSV"""
        failed = {}
        if os.path.exists(self.failed_log_file):
            try:
                with open(self.failed_log_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        file_key = f"{row['gazette_id']}_{row['language']}"
                        retry_count = int(row.get('retry_count', 0))
                        failed[file_key] = retry_count
            except Exception as e:
                self.logger.warning(f"Could not load failed log: {e}")
        return failed

    def is_already_processed(self, gazette_id, language):
        """Check if file has already been successfully archived"""
        file_key = f"{gazette_id}_{language}"
        return file_key in self.archived_files

    def should_retry_failed(self, gazette_id, language, max_retries=3):
        """Check if a failed file should be retried"""
        file_key = f"{gazette_id}_{language}"
        retry_count = self.failed_files.get(file_key, 0)
        return retry_count < max_retries

    def log_archived_file(self, gazette_id, date, language, description, file_path, file_size, status='SUCCESS'):
        """Log successfully archived file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.archive_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, gazette_id, date, language, description, file_path, file_size, status])

    def log_failed_file(self, gazette_id, date, language, description, url, error_reason):
        """Log failed file download"""
        file_key = f"{gazette_id}_{language}"
        retry_count = self.failed_files.get(file_key, 0) + 1
        self.failed_files[file_key] = retry_count
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.failed_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, gazette_id, date, language, description, url, error_reason, retry_count])

    def parse_date(self, date_str):
        """Parse date string and return year, month, day components"""
        try:
            # Assuming date format is YYYY-MM-DD or similar
            # Adjust this based on your actual date format
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
                self.logger.info(f"[EMPTY] {gazette_id} – No download links, only created folder. \n")
                # Log empty gazette entry
                self.log_archived_file(gazette_id, date, "none", desc, gazette_folder, 0, "EMPTY")
                continue

            for btn in pdf_buttons:
                
                full_lang_text = btn.css("button::text").get(default="unknown").strip().lower()
                short_code = self.lang_map.get(full_lang_text)
                
                if not short_code:
                    self.logger.warning(f"[UNKNOWN LANGUAGE] {full_lang_text} – Skipping.")
                    continue
                
                if self.lang != "all" and self.lang != short_code:
                    continue  # skip other languages

                # Check if already processed
                if self.is_already_processed(gazette_id, full_lang_text):
                    self.logger.info(f"[SKIPPED] {gazette_id} ({full_lang_text}) – Already archived")
                    continue

                # Check if should retry failed downloads
                if not self.should_retry_failed(gazette_id, full_lang_text):
                    self.logger.info(f"[SKIPPED] {gazette_id} ({full_lang_text}) – Max retries exceeded")
                    continue

                pdf_url = urljoin(response.url, btn.attrib["href"])
                file_path = os.path.join(gazette_folder, f"{gazette_id}_{full_lang_text}.pdf")

                yield scrapy.Request(
                    url=pdf_url,
                    callback=self.save_pdf,
                    meta={
                        "file_path": file_path,
                        "gazette_id": gazette_id,
                        "lang": full_lang_text,
                        "date": date,
                        "description": desc
                    },
                    errback=self.download_failed,
                    dont_filter=True
                )

    def save_pdf(self, response):
        path = response.meta["file_path"]
        gazette_id = response.meta["gazette_id"]
        lang = response.meta["lang"]
        date = response.meta["date"]
        description = response.meta["description"]
        
        try:
            with open(path, "wb") as f:
                f.write(response.body)
            
            file_size = len(response.body)
            self.logger.info(f"[SAVED] Gazette {gazette_id} ({lang}) – {file_size} bytes \n")
            
            # Log successful download
            self.log_archived_file(gazette_id, date, lang, description, path, file_size, "SUCCESS")
            
            # Add to archived files set to prevent re-downloading in same session
            file_key = f"{gazette_id}_{lang}"
            self.archived_files.add(file_key)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to save {gazette_id} ({lang}): {e}")
            self.log_failed_file(gazette_id, date, lang, description, response.url, f"Save error: {str(e)}")

    def download_failed(self, failure):
        request = failure.request
        gazette_id = request.meta.get("gazette_id", "unknown")
        lang = request.meta.get("lang", "unknown")
        date = request.meta.get("date", "unknown")
        description = request.meta.get("description", "unknown")
        
        error_reason = str(failure.value)
        self.logger.warning(f"[FAILED] {gazette_id} ({lang}) – {request.url} – {error_reason}")
        
        # Log failed download
        self.log_failed_file(gazette_id, date, lang, description, request.url, error_reason)

    def closed(self, reason):
        """Called when spider closes - print summary"""
        self.logger.info(f"Spider closed. Reason: {reason}")
        
        # Print summary statistics
        archived_count = len(self.archived_files)
        failed_count = len(self.failed_files)
        
        self.logger.info(f"SUMMARY for {self.year}:")
        self.logger.info(f"  - Successfully archived: {archived_count} files")
        self.logger.info(f"  - Failed downloads: {failed_count} files")
        self.logger.info(f"  - Archive log: {self.archive_log_file}")
        self.logger.info(f"  - Failed log: {self.failed_log_file}")