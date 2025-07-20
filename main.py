# from src.cmd import parse_args, identify_input_kind
# from pathlib import Path
# import yaml
# import sys
# from src.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure,create_folder_structure_on_cloud, upload_local_documents_to_gdrive, filter_pdf_only, save_upload_results,get_cloud_credentials
# from scrapy.crawler import CrawlerProcess
# from document_scraper.document_scraper import YearsSpider
# from document_scraper.document_scraper.spiders import DocMetadataSpider
# from document_scraper.document_scraper.spiders import PDFDownloaderSpider
# from googleapiclient.discovery import build


# def main():
#     # Hide logs (scrapy)
#     settings = hide_logs()
    
#     # Initiate crawling process
#     process = CrawlerProcess(settings=settings)
    
#     args = parse_args()
#     kind = identify_input_kind(args)

#     if kind == "invalid-input":
#         print("Invalid input! --year and --lang are required at minimum.")
#         sys.exit(1)
        
#     if kind == "invalid-lang-input":
#         print("Please enter supported language")
#         print("Supported languages: en (English), si (Sinhala), ta (Tamil)")
#         sys.exit(1)

#     # Project root
#     project_root = Path(__file__).parent

#     # Load config.yaml
#     with open(project_root / "config.yaml") as f:
#         config = yaml.safe_load(f)

#     # Resolve years.json path
#     output_path = project_root / config["output"]["years_json"]
#     output_path.parent.mkdir(parents=True, exist_ok=True)
    
#     # Resolve doc_metadata.json path
#     output_path_doc_metadata = project_root / config["output"]["doc_metadata_json"]
#     output_path_doc_metadata.parent.mkdir(parents=True, exist_ok=True)

#     # Step 1: Scrape latest year links and save to years.json
#     print("Checking for updates from the website...")    
#     process.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
#     print(f"Updated year metadata saved to {output_path}")
    
#     # Step 2: Validaate CLI --year against scraped data
#     metadata = load_years_metadata(output_path)
#     scraped_years = [entry["year"] for entry in metadata]
#     print(scraped_years)
#     if str(args.year) not in scraped_years:
#         print(f"Error: Year '{args.year}' is not available in scraped data.")
#         print(f"Available years: {', '.join(scraped_years)}")
#         sys.exit(1)

#     # Step 3: Continue processing with valid input
#     print(f"✅ Year '{args.year}' is valid.")
#     print(f"Input kind: {kind}")
#     print(f"Parameters: year={args.year}, month={args.month}, day={args.day}, lang={args.lang}")
    
#     # Get the URL corresponding to the relevant year
#     year_url = get_year_link(args.year, metadata)
    
#     if year_url:
#         print(f"✅ Year link: {year_url}")
#     else:
#         print("❌ Year not found in metadata.")
#         sys.exit(1)
        
#     # Step 4: Scrape the table metadata for the relevant year URL
#     process.crawl(DocMetadataSpider, url=year_url, lang=str(args.lang), output_path=str(output_path_doc_metadata))
    
#     # Step 5: Filter the metadata based on the input kind
#     doc_metadata = load_doc_metadata_file(output_path_doc_metadata)

#     filtered_doc_metadata, status = filter_doc_metadata(
#         doc_metadata, kind, 
#         year=str(args.year), 
#         month=str(args.month), 
#         date=str(args.day)
#         )
    
#     print(f"Status : {status}")
    
#     all_download_metadata = []
    
#     # Step 6: Create the folder structure for the filtered data and get download metadata
#     archive_location = config["archive"]["archive_location"]
#     all_download_metadata = create_folder_structure(archive_location, filtered_doc_metadata)
    
    
#     # Step 7: Download the documents
#     if all_download_metadata:
#         process.crawl(PDFDownloaderSpider, download_metadata=all_download_metadata)
#     else:
#         print("Byeeeeeeeee")
#         sys.exit(1)
    
#     # Start crawling
#     process.start()
        

#     # 🔑 Get the login credentials
#     your_credentials = get_cloud_credentials()
    
#     # Setup Google Drive API
#     service = build('drive', 'v3', credentials=your_credentials)
    
#     # Getting the upload metadata
#     upload_metadata = create_folder_structure_on_cloud(
#         service, 
#         filtered_doc_metadata, 
#         archive_location,
#         parent_folder_id=config["archive"]["g_drive_parent_folder_id"]  
#         )
    
#     # Filter the available docs
#     pdf_only_metadata = filter_pdf_only(upload_metadata)
    
#     # Upload the docs to cloud
#     results = upload_local_documents_to_gdrive(
#         service, 
#         pdf_only_metadata,
#         max_retries=3,
#         delay_between_uploads=1
#     )
    
    
#     upload_results = config["output"]["upload_results_json"]
#     save_upload_results(results, upload_results)
    
#     # Access specific results
#     print(f"Successful uploads: {results['successful_uploads']}")
#     print(f"Failed uploads: {results['failed_uploads']}")

#     # Get list of successful uploads with their Google Drive file IDs
#     successful_docs = [
#         detail for detail in results['upload_details'] 
#         if detail['status'] == 'success'
#     ]

#     for doc in successful_docs:
#         print(f"✅ {doc['doc_id']}: {doc['gdrive_file_id']}")
    
#     # : Call the correct downloader here based on input kind   
    
# if __name__ == "__main__":
#     main()
  


# from src.cmd import parse_args, identify_input_kind
# from pathlib import Path
# import yaml
# import sys
# from src.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure,create_folder_structure_on_cloud, upload_local_documents_to_gdrive, filter_pdf_only, save_upload_results,get_cloud_credentials
# from scrapy.crawler import CrawlerRunner
# from twisted.internet import reactor, defer
# from document_scraper.document_scraper import YearsSpider
# from document_scraper.document_scraper.spiders import DocMetadataSpider
# from document_scraper.document_scraper.spiders import PDFDownloaderSpider
# from googleapiclient.discovery import build


# @defer.inlineCallbacks
# def run_crawlers_sequentially(args, config, project_root):
#     """Run crawlers sequentially using CrawlerRunner"""
    
#     # Hide logs (scrapy)
#     settings = hide_logs()
    
#     # Initiate crawling runner
#     runner = CrawlerRunner(settings=settings)
    
#     # Resolve paths
#     output_path = project_root / config["output"]["years_json"]
#     output_path.parent.mkdir(parents=True, exist_ok=True)
    
#     output_path_doc_metadata = project_root / config["output"]["doc_metadata_json"]
#     output_path_doc_metadata.parent.mkdir(parents=True, exist_ok=True)

#     try:
#         # Step 1: Scrape latest year links and save to years.json
#         print("Checking for updates from the website...")    
#         yield runner.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
#         print(f"Updated year metadata saved to {output_path}")
        
#         # Step 2: Validate CLI --year against scraped data
#         metadata = load_years_metadata(output_path)
#         scraped_years = [entry["year"] for entry in metadata]
#         print(scraped_years)
        
#         if str(args.year) not in scraped_years:
#             print(f"Error: Year '{args.year}' is not available in scraped data.")
#             print(f"Available years: {', '.join(scraped_years)}")
#             reactor.stop()
#             return

#         # Step 3: Continue processing with valid input
#         print(f"✅ Year '{args.year}' is valid.")
#         print(f"Parameters: year={args.year}, month={args.month}, day={args.day}, lang={args.lang}")
        
#         # Get the URL corresponding to the relevant year
#         year_url = get_year_link(args.year, metadata)
        
#         if year_url:
#             print(f"✅ Year link: {year_url}")
#         else:
#             print("❌ Year not found in metadata.")
#             reactor.stop()
#             return
            
#         # Step 4: Scrape the table metadata for the relevant year URL
#         yield runner.crawl(DocMetadataSpider, url=year_url, lang=str(args.lang), output_path=str(output_path_doc_metadata))
        
#         # Step 5: Filter the metadata based on the input kind
#         doc_metadata = load_doc_metadata_file(output_path_doc_metadata)

#         filtered_doc_metadata, status = filter_doc_metadata(
#             doc_metadata, 
#             identify_input_kind(args), 
#             year=str(args.year), 
#             month=str(args.month), 
#             date=str(args.day)
#         )
        
#         print(f"Status : {status}")
        
#         # Step 6: Create the folder structure for the filtered data and get download metadata
#         archive_location = config["archive"]["archive_location"]
#         all_download_metadata = create_folder_structure(archive_location, filtered_doc_metadata)
        
#         # Step 7: Download the documents
#         if all_download_metadata:
#             yield runner.crawl(PDFDownloaderSpider, download_metadata=all_download_metadata)
#             print("✅ All crawlers completed successfully!")
#         else:
#             print("No documents to download")
            
#     except Exception as e:
#         print(f"Error during crawling: {e}")
#     finally:
#         # Continue with post-processing
#         yield defer.maybeDeferred(post_crawl_processing, args, config, filtered_doc_metadata, archive_location)


# def post_crawl_processing(args, config, filtered_doc_metadata, archive_location):
#     """Handle post-crawl processing (Google Drive upload, etc.)"""
#     try:
#         # 🔑 Get the login credentials
#         your_credentials = get_cloud_credentials()
        
#         # Setup Google Drive API
#         service = build('drive', 'v3', credentials=your_credentials)
        
#         # Getting the upload metadata
#         upload_metadata = create_folder_structure_on_cloud(
#             service, 
#             filtered_doc_metadata, 
#             archive_location,
#             parent_folder_id=config["archive"]["g_drive_parent_folder_id"]  
#         )
        
#         # Filter the available docs
#         pdf_only_metadata = filter_pdf_only(upload_metadata)
        
#         # Upload the docs to cloud
#         results = upload_local_documents_to_gdrive(
#             service, 
#             pdf_only_metadata,
#             max_retries=3,
#             delay_between_uploads=1
#         )
        
#         upload_results = config["output"]["upload_results_json"]
#         save_upload_results(results, upload_results)
        
#         # Access specific results
#         print(f"Successful uploads: {results['successful_uploads']}")
#         print(f"Failed uploads: {results['failed_uploads']}")

#         # Get list of successful uploads with their Google Drive file IDs
#         successful_docs = [
#             detail for detail in results['upload_details'] 
#             if detail['status'] == 'success'
#         ]

#         for doc in successful_docs:
#             print(f"✅ {doc['doc_id']}: {doc['gdrive_file_id']}")
            
#     except Exception as e:
#         print(f"Error during post-processing: {e}")
#     finally:
#         reactor.stop()


# def main():
#     args = parse_args()
#     kind = identify_input_kind(args)

#     if kind == "invalid-input":
#         print("Invalid input! --year and --lang are required at minimum.")
#         sys.exit(1)
        
#     if kind == "invalid-lang-input":
#         print("Please enter supported language")
#         print("Supported languages: en (English), si (Sinhala), ta (Tamil)")
#         sys.exit(1)

#     # Project root
#     project_root = Path(__file__).parent

#     # Load config.yaml
#     with open(project_root / "config.yaml") as f:
#         config = yaml.safe_load(f)

#     # Run crawlers sequentially
#     run_crawlers_sequentially(args, config, project_root)
#     reactor.run()


# if __name__ == "__main__":
#     main()


# Install asyncio reactor before importing scrapy
import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Install the asyncio reactor
from twisted.internet import asyncioreactor
asyncioreactor.install()

from src.cmd import parse_args, identify_input_kind
from pathlib import Path
import yaml
from src.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure,create_folder_structure_on_cloud, upload_local_documents_to_gdrive, filter_pdf_only, save_upload_results,get_cloud_credentials
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer
from document_scraper.document_scraper import YearsSpider
from document_scraper.document_scraper.spiders import DocMetadataSpider
from document_scraper.document_scraper.spiders import PDFDownloaderSpider
from googleapiclient.discovery import build


@defer.inlineCallbacks
def run_crawlers_sequentially(args, config, project_root):
    """Run crawlers sequentially using CrawlerRunner"""
    
    # Hide logs (scrapy)
    settings = hide_logs()
    
    # Initiate crawling runner
    runner = CrawlerRunner(settings=settings)
    
    # Resolve paths
    output_path = project_root / config["output"]["years_json"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_path_doc_metadata = project_root / config["output"]["doc_metadata_json"]
    output_path_doc_metadata.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Scrape latest year links and save to years.json
        print("Checking for updates from the website...")    
        yield runner.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
        print(f"Updated year metadata saved to {output_path}")
        
        # Step 2: Validate CLI --year against scraped data
        metadata = load_years_metadata(output_path)
        scraped_years = [entry["year"] for entry in metadata]
        print(scraped_years)
        
        if str(args.year) not in scraped_years:
            print(f"Error: Year '{args.year}' is not available in scraped data.")
            print(f"Available years: {', '.join(scraped_years)}")
            reactor.stop()
            return

        # Step 3: Continue processing with valid input
        print(f"✅ Year '{args.year}' is valid.")
        print(f"Parameters: year={args.year}, month={args.month}, day={args.day}, lang={args.lang}")
        
        # Get the URL corresponding to the relevant year
        year_url = get_year_link(args.year, metadata)
        
        if year_url:
            print(f"✅ Year link: {year_url}")
        else:
            print("❌ Year not found in metadata.")
            reactor.stop()
            return
            
        # Step 4: Scrape the table metadata for the relevant year URL
        yield runner.crawl(DocMetadataSpider, url=year_url, lang=str(args.lang), output_path=str(output_path_doc_metadata))
        
        # Step 5: Filter the metadata based on the input kind
        doc_metadata = load_doc_metadata_file(output_path_doc_metadata)

        filtered_doc_metadata, status = filter_doc_metadata(
            doc_metadata, 
            identify_input_kind(args), 
            year=str(args.year), 
            month=str(args.month), 
            date=str(args.day)
        )
        
        print(f"Status : {status}")
        
        # Step 6: Create the folder structure for the filtered data and get download metadata
        archive_location = config["archive"]["archive_location"]
        all_download_metadata = create_folder_structure(archive_location, filtered_doc_metadata)
        
        # Step 7: Download the documents
        if all_download_metadata:
            yield runner.crawl(PDFDownloaderSpider, download_metadata=all_download_metadata)
            print("✅ All crawlers completed successfully!")
        else:
            print("No documents to download")
            
    except Exception as e:
        print(f"Error during crawling: {e}")
    finally:
        # Continue with post-processing
        yield defer.maybeDeferred(post_crawl_processing, args, config, filtered_doc_metadata, archive_location)


def post_crawl_processing(args, config, filtered_doc_metadata, archive_location):
    """Handle post-crawl processing (Google Drive upload, etc.)"""
    try:
        # 🔑 Get the login credentials
        your_credentials = get_cloud_credentials()
        
        # Setup Google Drive API
        service = build('drive', 'v3', credentials=your_credentials)
        
        # Getting the upload metadata
        upload_metadata = create_folder_structure_on_cloud(
            service, 
            filtered_doc_metadata, 
            archive_location,
            parent_folder_id=config["archive"]["g_drive_parent_folder_id"]  
        )
        
        # Filter the available docs
        pdf_only_metadata = filter_pdf_only(upload_metadata)
        
        # Upload the docs to cloud
        results = upload_local_documents_to_gdrive(
            service, 
            pdf_only_metadata,
            max_retries=3,
            delay_between_uploads=1
        )
        
        upload_results = config["output"]["upload_results_json"]
        save_upload_results(results, upload_results)
        
        # Access specific results
        print(f"Successful uploads: {results['successful_uploads']}")
        print(f"Failed uploads: {results['failed_uploads']}")

        # Get list of successful uploads with their Google Drive file IDs
        successful_docs = [
            detail for detail in results['upload_details'] 
            if detail['status'] == 'success'
        ]

        for doc in successful_docs:
            print(f"✅ {doc['doc_id']}: {doc['gdrive_file_id']}")
            
    except Exception as e:
        print(f"Error during post-processing: {e}")
    finally:
        reactor.stop()


def main():
    args = parse_args()
    kind = identify_input_kind(args)

    if kind == "invalid-input":
        print("Invalid input! --year and --lang are required at minimum.")
        sys.exit(1)
        
    if kind == "invalid-lang-input":
        print("Please enter supported language")
        print("Supported languages: en (English), si (Sinhala), ta (Tamil)")
        sys.exit(1)

    # Project root
    project_root = Path(__file__).parent

    # Load config.yaml
    with open(project_root / "config.yaml") as f:
        config = yaml.safe_load(f)

    # Run crawlers sequentially
    run_crawlers_sequentially(args, config, project_root)
    reactor.run()


if __name__ == "__main__":
    main()