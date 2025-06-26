import os
import scrapy
from urllib.parse import urljoin
from pathlib import Path
import json
import csv
from datetime import datetime
from tqdm import tqdm
import logging
import signal
import sys
import tempfile
import atexit
from scrapy import signals
from scrapy.exceptions import CloseSpider

class GazetteDownloadSpider(scrapy.Spider):
    name = "gazette_download"
    start_urls = []

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "%(levelname)s: %(message)s",
        "LOG_STDOUT": False,
        # Handle data loss gracefully instead of failing
        "DOWNLOAD_FAIL_ON_DATALOSS": False,
        # Disable the generator return value warning
        "WARN_ON_GENERATOR_RETURN_VALUE": False,
    }
    
    def __init__(self, year=None, year_url=None, lang="all", *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize crawler and settings attributes to None - will be set by from_crawler
        self.crawler = None
        self.settings = None
        
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
        
        # Progress tracking
        self.total_gazettes = 0
        self.processed_gazettes = 0
        self.total_downloads = 0
        self.completed_downloads = 0
        self.skipped_downloads = 0
        self.failed_downloads = 0
        self.progress_bar = None
        
        # Track ongoing downloads for cleanup
        self.ongoing_downloads = set()
        
        # Graceful shutdown flags
        self.shutdown_requested = False
        self.graceful_shutdown = False
        
        # Setup signal handlers and cleanup
        self.setup_signal_handlers()
        self.setup_file_logger()
        
        # Register cleanup function to run on exit
        atexit.register(self.emergency_cleanup)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)
        # Set the crawler reference so spider can access settings
        spider.crawler = crawler
        spider.settings = crawler.settings  # Add this line to fix the settings issue
        # Connect the spider_closed signal
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            if self.shutdown_requested:
                # If already shutting down and user presses Ctrl+C again, force exit
                print(f"\n🛑 Force shutdown requested...")
                self.force_cleanup()
                sys.exit(1)
            
            print(f"\n🛑 Received interrupt signal. Finishing current downloads...")
            self.shutdown_requested = True
            self.graceful_shutdown = True
            
            if hasattr(self, 'crawler') and self.crawler:
                # Tell Scrapy to stop gracefully
                self.crawler.engine.close_spider(self, 'User requested shutdown')
            else:
                # Fallback cleanup if crawler not available
                self.cleanup_and_exit()
        
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Kill command

    def cleanup_and_exit(self):
        """Perform cleanup and exit"""
        print("🧹 Cleaning up...")
        self.cleanup_partial_downloads()
        
        if self.progress_bar:
            self.progress_bar.close()
        
        print("✅ Graceful shutdown complete. Progress saved - you can resume later.")
        print(f"📊 Downloaded: {self.completed_downloads}, Failed: {self.failed_downloads}")
        sys.exit(0)

    def force_cleanup(self):
        """Emergency cleanup for force shutdown"""
        try:
            self.cleanup_partial_downloads()
            if self.progress_bar:
                self.progress_bar.close()
        except:
            pass

    def emergency_cleanup(self):
        """Emergency cleanup function registered with atexit"""
        if not self.graceful_shutdown:
            self.cleanup_partial_downloads()

    def cleanup_partial_downloads(self):
        """Clean up any partial downloads that were in progress"""
        cleaned_count = 0
        for file_path in self.ongoing_downloads.copy():
            try:
                if os.path.exists(file_path):
                    # Check if file is likely incomplete (very small size)
                    file_size = os.path.getsize(file_path)
                    if file_size < 1024:  # Files smaller than 1KB are likely incomplete
                        os.remove(file_path)
                        cleaned_count += 1
                        if hasattr(self, 'file_logger'):
                            self.file_logger.info(f"Cleaned up partial download: {file_path}")
                
                # Also clean up .tmp files
                temp_path = file_path + ".tmp"
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    cleaned_count += 1
                    
                self.ongoing_downloads.remove(file_path)
            except Exception as e:
                if hasattr(self, 'file_logger'):
                    self.file_logger.warning(f"Could not clean up {file_path}: {e}")
        
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} partial downloads")

    def setup_file_logger(self):
        """Setup a separate file logger for detailed logging"""
        log_file = os.path.join(self.year_folder, f"{self.year}_spider_log.txt")
        self.file_logger = logging.getLogger(f'gazette_spider_{self.year}')
        self.file_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.file_logger.handlers[:]:
            self.file_logger.removeHandler(handler)
        
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        self.file_logger.addHandler(handler)

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

    def is_file_complete_and_valid(self, file_path, min_size=1024):
        """Check if a downloaded file is complete and valid"""
        try:
            if not os.path.exists(file_path):
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size < min_size:  # Files smaller than 1KB are likely incomplete
                return False
            
            # Basic PDF validation - check if it starts with PDF header
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False
            
            return True
        except Exception:
            return False

    def load_archived_files(self):
        """Load list of already archived files from CSV"""
        archived = set()
        if os.path.exists(self.archive_log_file):
            try:
                with open(self.archive_log_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['status'] == 'SUCCESS':
                            # Verify the file still exists and is valid
                            file_path = row.get('file_path', '')
                            if file_path and self.is_file_complete_and_valid(file_path):
                                # Create unique identifier: gazette_id + language
                                file_key = f"{row['gazette_id']}_{row['language']}"
                                archived.add(file_key)
                            else:
                                # File is missing or corrupted, allow re-download
                                if hasattr(self, 'file_logger'):
                                    self.file_logger.warning(f"File missing or corrupted, will re-download: {file_path}")
            except Exception as e:
                print(f"Warning: Could not load archive log: {e}")
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
                print(f"Warning: Could not load failed log: {e}")
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
                    if hasattr(self, 'file_logger'):
                        self.file_logger.warning(f"Could not parse date: {date_str}, using current date")
                    now = datetime.now()
                    return now.year, now.month, now.day

    def parse(self, response):
        # Check if shutdown was requested
        if self.shutdown_requested:
            self.file_logger.info("Shutdown requested during parsing, stopping")
            raise CloseSpider('User requested shutdown')
        
        rows = response.css("table tbody tr")
        self.total_gazettes = len(rows)
        
        # Count total downloads first (excluding already processed)
        print(f"🔍 Analyzing {self.total_gazettes} gazette entries...")
        potential_downloads = 0
        already_processed_count = 0
        
        for row in rows:
            gazette_id = row.css("td:nth-child(1)::text").get(default="").strip().replace("/", "-")
            download_cell = row.css("td:nth-child(4)")
            pdf_buttons = download_cell.css("a")
            
            for btn in pdf_buttons:
                full_lang_text = btn.css("button::text").get(default="unknown").strip().lower()
                short_code = self.lang_map.get(full_lang_text)
                
                if not short_code:
                    continue
                
                if self.lang != "all" and self.lang != short_code:
                    continue
                
                potential_downloads += 1
                
                # Check if already processed
                if self.is_already_processed(gazette_id, full_lang_text):
                    already_processed_count += 1
                elif not self.should_retry_failed(gazette_id, full_lang_text):
                    already_processed_count += 1
                else:
                    self.total_downloads += 1
        
        # Initialize progress bar with clean format
        self.progress_bar = tqdm(
            total=self.total_downloads,
            desc="📥 Downloading",
            unit="files",
            bar_format="{desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} [{rate_fmt}]",
            position=0,
            leave=True
        )
        
        print(f"\n📊 Analysis complete:")
        print(f"   • {potential_downloads} total files match your language filter")
        print(f"   • {already_processed_count} already processed (skipping)")
        print(f"   • {self.total_downloads} files to download")
        print(f"💡 Press Ctrl+C to gracefully stop after current downloads complete")
        self.file_logger.info(f"Found {self.total_gazettes} gazette entries, {potential_downloads} potential downloads, {self.total_downloads} new downloads needed")

        for row in rows:
            # Check for shutdown request before processing each gazette
            if self.shutdown_requested:
                self.file_logger.info("Shutdown requested, stopping gazette processing")
                break
                
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
                self.file_logger.info(f"[EMPTY] {gazette_id} – No download links, only created folder.")
                # Log empty gazette entry
                self.log_archived_file(gazette_id, date, "none", desc, gazette_folder, 0, "EMPTY")
                self.processed_gazettes += 1
                continue
            
            for btn in pdf_buttons:
                # Check for shutdown request before each download
                if self.shutdown_requested:
                    self.file_logger.info("Shutdown requested, stopping download requests")
                    return
                
                full_lang_text = btn.css("button::text").get(default="unknown").strip().lower()
                short_code = self.lang_map.get(full_lang_text)
                
                if not short_code:
                    self.file_logger.warning(f"[UNKNOWN LANGUAGE] {full_lang_text} – Skipping.")
                    continue
                
                if self.lang != "all" and self.lang != short_code:
                    continue  # skip other languages
                
                # Check if already processed
                if self.is_already_processed(gazette_id, full_lang_text):
                    self.file_logger.info(f"[SKIPPED] {gazette_id} ({full_lang_text}) – Already archived")
                    self.skipped_downloads += 1
                    self.update_progress_bar("skip")
                    continue

                # Check if should retry failed downloads
                if not self.should_retry_failed(gazette_id, full_lang_text):
                    self.file_logger.info(f"[SKIPPED] {gazette_id} ({full_lang_text}) – Max retries exceeded")
                    self.skipped_downloads += 1
                    self.update_progress_bar("skip")
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
                
            self.processed_gazettes += 1
            
    def update_progress_bar(self, action="download"):
        """Update progress bar with minimal distraction"""
        if self.progress_bar:
            if action == "download":
                self.completed_downloads += 1
            elif action == "skip":
                # Don't increment here - we're only tracking skips that were counted in total_downloads
                pass
            elif action == "fail":
                self.failed_downloads += 1
            
            # Update progress (only count actual downloads and failures against the total)
            completed = self.completed_downloads + self.failed_downloads
            self.progress_bar.n = completed
            
            # Update description with current stats
            desc = f"📥 Downloaded: {self.completed_downloads}"
            if self.failed_downloads > 0:
                desc += f" | ❌ Failed: {self.failed_downloads}"
            self.progress_bar.set_description(desc[:50])  # Shorter description
            self.progress_bar.refresh()

    def save_pdf(self, response):
        # Check if shutdown was requested
        if self.shutdown_requested:
            self.file_logger.info("Shutdown requested, skipping save_pdf")
            return
            
        path = response.meta["file_path"]
        gazette_id = response.meta["gazette_id"]
        lang = response.meta["lang"]
        date = response.meta["date"]
        description = response.meta["description"]
        
        # Add to ongoing downloads tracking
        self.ongoing_downloads.add(path)
        
        try:
            # Use temporary file to ensure atomic write
            temp_path = path + ".tmp"
            
            with open(temp_path, "wb") as f:
                f.write(response.body)
            
            # Verify the download is complete and valid
            if self.is_file_complete_and_valid(temp_path):
                # Move from temp to final location (atomic operation)
                os.rename(temp_path, path)
                
                file_size = len(response.body)
                
                # Log successful download
                self.log_archived_file(gazette_id, date, lang, description, path, file_size, "SUCCESS")
                self.file_logger.info(f"[SAVED] Gazette {date} {gazette_id} ({lang}) – {file_size} bytes")
                
                # Add to archived files set to prevent re-downloading in same session
                file_key = f"{gazette_id}_{lang}"
                self.archived_files.add(file_key)
                
                # Update progress
                self.update_progress_bar("download")
            else:
                # File is invalid, clean up and log as failed
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise Exception("Downloaded file is invalid or corrupted")
                
        except Exception as e:
            # Clean up any temp files
            temp_path = path + ".tmp"
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            self.file_logger.error(f"[ERROR] Failed to save Gazette {date} {gazette_id} ({lang}): {e}")
            self.log_failed_file(gazette_id, date, lang, description, response.url, f"Save error: {str(e)}")
            self.update_progress_bar("fail")
        finally:
            # Remove from ongoing downloads
            self.ongoing_downloads.discard(path)

    def download_failed(self, failure):
        request = failure.request
        gazette_id = request.meta.get("gazette_id", "unknown")
        lang = request.meta.get("lang", "unknown")
        date = request.meta.get("date", "unknown")
        description = request.meta.get("description", "unknown")
        
        error_reason = str(failure.value)
        self.file_logger.warning(f"[FAILED] {gazette_id} ({lang}) – {request.url} – {error_reason}")
        
        # Log failed download
        self.log_failed_file(gazette_id, date, lang, description, request.url, error_reason)
        
        # Update progress
        self.update_progress_bar("fail")

    def spider_closed(self, spider, reason):
        """Called when spider closes via Scrapy's signal system"""
        self.graceful_shutdown = True
        self.closed(reason)

    def closed(self, reason):
        """Called when spider closes - print summary"""
        # Clean up any ongoing downloads
        self.cleanup_partial_downloads()
        
        # Close progress bar
        if self.progress_bar:
            self.progress_bar.close()
            
        # Clear line and print final summary
        print("\n" + "=" * 60)
        print(f"🎯 DOWNLOAD SUMMARY for {self.year}")
        print("=" * 60)
        print(f"📊 Total gazette entries: {self.processed_gazettes}/{self.total_gazettes}")
        print(f"✅ Successfully downloaded: {self.completed_downloads} files")
        if self.skipped_downloads > 0:
            print(f"⏭️  Skipped (already archived): {self.skipped_downloads} files")
        if self.failed_downloads > 0:
            print(f"❌ Failed downloads: {self.failed_downloads} files")
        total_processed = self.completed_downloads + self.skipped_downloads + self.failed_downloads
        print(f"📁 Total files processed: {total_processed}")
        print("=" * 60)
        print(f"📄 Archive log: {self.archive_log_file}")
        print(f"🚫 Failed log: {self.failed_log_file}")
        print(f"📋 Detailed log: {os.path.join(self.year_folder, f'{self.year}_spider_log.txt')}")
        
        # Add resumption info
        if reason in ['cancelled', 'shutdown', 'User requested shutdown']:
            print("🔄 Download was interrupted - you can resume by running the same command again")
        elif self.failed_downloads > 0:
            print("🔄 Some downloads failed - run again to retry failed downloads")
        
        print("=" * 60)
        
        # Log summary to file as well
        self.file_logger.info(f"Spider closed. Reason: {reason}")
        self.file_logger.info(f"SUMMARY - Processed: {self.processed_gazettes}, Downloaded: {self.completed_downloads}, Skipped: {self.skipped_downloads}, Failed: {self.failed_downloads}")