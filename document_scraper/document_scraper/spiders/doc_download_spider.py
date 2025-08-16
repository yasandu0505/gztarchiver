import scrapy
from pathlib import Path
import csv

class PDFDownloaderSpider(scrapy.Spider):
    name = "pdf_downloader"
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS": 2,
        "RETRY_ENABLED": True,
        "LOG_LEVEL": "ERROR"
    }

    def __init__(self, download_metadata=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.download_metadata = download_metadata or []
        self.archived_docs = set()
        self.failed_docs = set()

    def check_available_data(self):
        """
        Check archived and failed log files to determine what needs to be downloaded.
        Returns filtered metadata with items that need to be processed.
        """
        # Group metadata by year to check respective log files
        year_groups = {}
        for item in self.download_metadata:
            try:
                year = item["file_path"].parts[-5]  # Extract year from the path
                if year not in year_groups:
                    year_groups[year] = []
                year_groups[year].append(item)
            except (IndexError, AttributeError):
                self.logger.warning(f"Could not extract year from path: {item.get('file_path', 'unknown')}")
                print(f"Could not extract year from path: {item.get('file_path', 'unknown')}")
                # Add to a default group if year extraction fails
                if 'unknown' not in year_groups:
                    year_groups['unknown'] = []
                year_groups['unknown'].append(item)

        # Check each year's log files
        for year, items in year_groups.items():
            if year == 'unknown':
                continue
                
            # Get base log directory for this year
            base_log_dir = Path(items[0]["file_path"]).parents[4] / year
            
            # Check archived logs
            archived_log_file = base_log_dir / "archived_logs.csv"
            if archived_log_file.exists():
                self.archived_docs.update(self._read_log_file(archived_log_file))
                self.logger.info(f"📋 Found {len(self.archived_docs)} archived documents for {year}")
                print(f"📋 Found {len(self.archived_docs)} archived documents for {year}")

            # Check failed logs
            failed_log_file = base_log_dir / "failed_logs.csv"
            if failed_log_file.exists():
                self.failed_docs.update(self._read_log_file(failed_log_file))
                self.logger.info(f"🔄 Found {len(self.failed_docs)} failed documents for {year}")
                print(f"🔄 Found {len(self.failed_docs)} failed documents for {year}")

        # Filter metadata based on archived and failed logs
        filtered_metadata = []
        unavailable_items = []
        skipped_count = 0
        retry_count = 0

        for item in self.download_metadata:
            doc_id = item.get("doc_id")
            url = item.get("download_url")
            
            if doc_id in self.archived_docs:
                # Skip already archived documents
                skipped_count += 1
                self.logger.debug(f"⏭️ Skipping archived document: {doc_id}")
                print(f"⏭️ Skipping archived document: {doc_id}")
                continue
            elif not url or url == "N/A":
                # Separate unavailable items (no valid URL)
                unavailable_items.append(item)
                continue
            elif doc_id in self.failed_docs:
                # Retry failed documents
                retry_count += 1
                self.logger.info(f"🔄 Retrying failed document: {doc_id}")
                print(f"🔄 Retrying failed document: {doc_id}")
                filtered_metadata.append(item)
            else:
                # New document to download
                filtered_metadata.append(item)

        # Process unavailable items separately
        if unavailable_items:
            self.logger.info(f"⚠️ Processing {len(unavailable_items)} unavailable documents:")
            print(f"⚠️ Processing {len(unavailable_items)} unavailable documents:")
            for item in unavailable_items:
                # Create folder structure
                folder_path = item["file_path"].parent
                folder_path.mkdir(parents=True, exist_ok=True)
                
                # Log to unavailable.csv
                self.log_status(item, "unavailable_logs")
                self.logger.info(f"⚠️ Unavailable: {item['doc_id']}")
                print(f"⚠️ Unavailable: {item['doc_id']}")
                

        self.logger.info(f"📊 Data check summary:")
        self.logger.info(f"   - Total documents: {len(self.download_metadata)}")
        self.logger.info(f"   - Already archived (skipped): {skipped_count}")
        self.logger.info(f"   - Unavailable (no download URL): {len(unavailable_items)}")
        self.logger.info(f"   - Failed (retrying): {retry_count}")
        self.logger.info(f"   - New to download: {len(filtered_metadata) - retry_count}")
        self.logger.info(f"   - Total to download: {len(filtered_metadata)}")
        print(f"📊 Data check summary:")
        print(f"   - Total documents: {len(self.download_metadata)}")
        print(f"   - Already archived (skipped): {skipped_count}")
        print(f"   - Unavailable (no download URL): {len(unavailable_items)}")
        print(f"   - Failed (retrying): {retry_count}")
        print(f"   - New to download: {len(filtered_metadata) - retry_count}")
        print(f"   - Total to download: {len(filtered_metadata)}")

        return filtered_metadata

    def _read_log_file(self, log_file_path):
        """Read doc_ids from a log file and return as a set."""
        doc_ids = set()
        try:
            with open(log_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    doc_id = row.get('doc_id')
                    if doc_id:
                        doc_ids.add(doc_id)
        except Exception as e:
            self.logger.error(f"❌ Error reading log file {log_file_path}: {e}")
            print(f"❌ Error reading log file {log_file_path}: {e}")
        return doc_ids

    def start_requests(self):
        # Check available data before starting downloads
        self.logger.info("🔍 Checking available data...")
        filtered_metadata = self.check_available_data()
        
        for item in filtered_metadata:
            url = item.get("download_url")
            # Since we already filtered out unavailable items, all items here should have valid URLs
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
            self.log_status(item, "archived_logs")
            self.logger.info(f"✅ Downloaded: {file_path}")
            print(f"✅ Downloaded: {file_path}")
        except Exception as e:
            self.log_status(item, "failed_logs")
            self.logger.error(f"❌ Failed to save {file_path}: {e}")
            print(f"❌ Failed to save {file_path}: {e}")

    def handle_failure(self, failure):
        item = failure.request.meta["item"]
        self.log_status(item, "failed_logs")
        self.logger.error(f"❌ Request failed: {item['download_url']}")
        print(f"❌ Request failed: {item['download_url']}")

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
            print(f"❌ Failed to log status for {item.get('doc_id', 'unknown')}: {e}")