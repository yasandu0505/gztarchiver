from doc_scraper.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure,create_folder_structure_on_cloud, upload_local_documents_to_gdrive, filter_pdf_only, save_upload_results, get_cloud_credentials, prepare_metadata_for_db, connect_to_db, insert_docs_by_year
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer
from document_scraper.document_scraper import YearsSpider
from document_scraper.document_scraper.spiders import DocMetadataSpider
from document_scraper.document_scraper.spiders import PDFDownloaderSpider
from doc_inspector.utils import extract_text_from_pdf, prepare_for_llm_processing, save_classified_doc_metadata, prepare_classified_metadata
from googleapiclient.discovery import build
import json
from pathlib import Path
from datetime import datetime

@defer.inlineCallbacks
def run_crawlers_sequentially(args, config, user_input_kind):
    """Run crawlers sequentially using CrawlerRunner"""
    
    # Hide logs (scrapy)
    settings = hide_logs()
    
    # Initiate crawling runner
    runner = CrawlerRunner(settings=settings)
    
    # Resolve paths
    output_path = config["output"]["years_json"]
    OUTPUT_PATH = Path(output_path)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    output_path_doc_metadata = config["output"]["doc_metadata_json"]
    OUTPUT_PATH_DOC_METADATA = Path(output_path_doc_metadata)
    OUTPUT_PATH_DOC_METADATA.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Scrape latest year links and save to years.json
        print("Checking for updates from the website...")    
        yield runner.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
        print(f"Updated year metadata saved to {output_path}")
        
        # Step 2: Validate CLI --year against scraped data
        metadata = load_years_metadata(output_path)
        scraped_years = [entry["year"] for entry in metadata]
        
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
            user_input_kind, 
            year=str(args.year), 
            month=str(args.month),
            date=str(args.day)
        )
        
        print(f"Status : {status}")
        
        # Step 6: Create the folder structure for the filtered data and get download metadata
        archive_location = config["archive"]["archive_location"]
        ARCHIHVE_LOCATION = Path(archive_location)
        all_download_metadata = create_folder_structure(ARCHIHVE_LOCATION, filtered_doc_metadata)
                        
        # Step 7: Download the documents
        if all_download_metadata:
            yield runner.crawl(PDFDownloaderSpider, download_metadata=all_download_metadata)
            print("✅ All crawlers completed successfully!")
            yield defer.maybeDeferred(post_crawl_processing, args, config, all_download_metadata, archive_location)
        else:
            print("No documents to download")
            
    except Exception as e:
        print(f"Error during crawling: {e}")
    finally:
        # Continue with post-processing
        reactor.stop()

# TODO: i have to send filtered_doc_metadata instead of the upload_metadata , otherwise if the create_folder_structure_on_cloud fails , the program stops from there.
def post_crawl_processing(args, config, all_download_metadata, archive_location):
    """Handle post-crawl processing (Data preprocessing, etc.)"""
    try:
        # Extract data from the pdf files      
        extracted_texts = extract_text_from_pdf(all_download_metadata)
        
        # Preprocess the extracted data to be used on LLM
        llm_ready_texts = prepare_for_llm_processing(extracted_texts)
        
        api_key = config["credentials"]["deepseek_api_key"]
        
        # TODO : we can achive this using only a dictionary (no need of bot list and dic)
        # Classification process of the pdfs'
        classified_metadata, classified_metadata_dic = prepare_classified_metadata(llm_ready_texts, api_key)
       
        # BUG : data is not relaiable, issue when saving, rewrite the whole file again in the next run   
        # Saving the classified metadata of the pdfs'
        save_classified_doc_metadata(classified_metadata, archive_location, args.year)
        
        # Processing metadata to upload to the database
        prepared_metadata_to_store = prepare_metadata_for_db(all_download_metadata, classified_metadata_dic)
        
        # Establish db connection and upload process        
        uri = config["db_credentials"]["mongo_db_uri"]
        
        client = connect_to_db(uri)
        
        # TODO : update the schema of the backend for CRUD
        if client:
            db = client["doc_db"]
            insert_docs_by_year(db, prepared_metadata_to_store, args.year)
        else:
            print("❌ Failed uploading to the mongodb")
            
    except Exception as e:
        print(f"Error during post-processing: {e}")