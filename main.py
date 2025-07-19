from src.cmd import parse_args, identify_input_kind
from pathlib import Path
import yaml
import sys
from src.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure,create_folder_structure_on_cloud, upload_local_documents_to_gdrive, filter_pdf_only, save_upload_results
from scrapy.crawler import CrawlerProcess
from document_scraper.document_scraper import YearsSpider
from document_scraper.document_scraper.spiders import DocMetadataSpider
from document_scraper.document_scraper.spiders import PDFDownloaderSpider
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import os

# This permission scope lets your program access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# This function helps you log in and get credentials
def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def main():
    # Hide logs (scrapy)
    settings = hide_logs()
    
    # Initiate crawling process
    process = CrawlerProcess(settings=settings)
    
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

    # Resolve years.json path
    output_path = project_root / config["output"]["years_json"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Resolve doc_metadata.json path
    output_path_doc_metadata = project_root / config["output"]["doc_metadata_json"]
    output_path_doc_metadata.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Scrape latest year links and save to years.json
    print("Checking for updates from the website...")    
    process.crawl(YearsSpider, url=config["scrape"]["url"], output_path=str(output_path))
    print(f"Updated year metadata saved to {output_path}")
    
    # Step 2: Validaate CLI --year against scraped data
    metadata = load_years_metadata(output_path)
    scraped_years = [entry["year"] for entry in metadata]
    print(scraped_years)
    if str(args.year) not in scraped_years:
        print(f"Error: Year '{args.year}' is not available in scraped data.")
        print(f"Available years: {', '.join(scraped_years)}")
        sys.exit(1)

    # Step 3: Continue processing with valid input
    print(f"✅ Year '{args.year}' is valid.")
    print(f"Input kind: {kind}")
    print(f"Parameters: year={args.year}, month={args.month}, day={args.day}, lang={args.lang}")
    
    # Get the URL corresponding to the relevant year
    year_url = get_year_link(args.year, metadata)
    
    if year_url:
        print(f"✅ Year link: {year_url}")
    else:
        print("❌ Year not found in metadata.")
        sys.exit(1)
        
    # Step 4: Scrape the table metadata for the relevant year URL
    process.crawl(DocMetadataSpider, url=year_url, lang=str(args.lang), output_path=str(output_path_doc_metadata))
    
    # Step 5: Filter the metadata based on the input kind
    doc_metadata = load_doc_metadata_file(output_path_doc_metadata)

    filtered_doc_metadata, status = filter_doc_metadata(
        doc_metadata, kind, 
        year=str(args.year), 
        month=str(args.month), 
        date=str(args.day)
        )
    
    print(f"Status : {status}")
    
    all_download_metadata = []
    
    # Step 6: Create the folder structure for the filtered data and get download metadata
    archive_location = config["archive"]["archive_location"]
    all_download_metadata = create_folder_structure(archive_location, filtered_doc_metadata)
    
    
    
    # Step 7: Download the documents
    if all_download_metadata:
        process.crawl(PDFDownloaderSpider, download_metadata=all_download_metadata)
    else:
        print("Byeeeeeeeee")
        sys.exit(1)
        
    # Start crawling
    process.start()
    
    # 🔑 Get the login credentials
    your_credentials = get_credentials()
    
    # Setup Google Drive API
    service = build('drive', 'v3', credentials=your_credentials)
    
    upload_metadata = create_folder_structure_on_cloud(
        service, 
        filtered_doc_metadata, 
        archive_location,
        parent_folder_id=config["archive"]["g_drive_parent_folder_id"]  # or None for root
        )
    
    for doc in upload_metadata:
        print(doc)
        print("/n")
        

    pdf_only_metadata = filter_pdf_only(upload_metadata)
    
    results = upload_local_documents_to_gdrive(
        service, 
        pdf_only_metadata,
        max_retries=3,
        delay_between_uploads=1
    )
    
    save_upload_results(results, "upload_results.json")
    
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
    
    # : Call the correct downloader here based on input kind   
    
if __name__ == "__main__":
    main()
  

