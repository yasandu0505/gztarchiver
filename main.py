from src.cmd import parse_args, identify_input_kind
from pathlib import Path
import yaml
import sys
from src.utils import load_years_metadata, get_year_link, hide_logs, load_doc_metadata_file, filter_doc_metadata, create_folder_structure
from scrapy.crawler import CrawlerProcess
from document_scraper.document_scraper import YearsSpider
from document_scraper.document_scraper.spiders import DocMetadataSpider

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
    
    # Start crawling
    process.start()
    
    # Step 5: Filter the metadata based on the input kind
    doc_metadata = load_doc_metadata_file(output_path_doc_metadata)

    filtered_doc_metadata, status = filter_doc_metadata(
        doc_metadata, kind, 
        year=str(args.year), 
        month=str(args.month), 
        date=str(args.day)
        )
    
    print(status)
    for doc in filtered_doc_metadata:
        print(doc)
        
    # Step 6: Create the folder structure for the filtered data
    archive_location = config["archive"]["archive_location"]
    
    create_folder_structure(archive_location, filtered_doc_metadata)
    
        
    
        
    
    
    
    
    
    
        
    # : Call the correct downloader here based on input kind   
    
    
# # Test dataset - sample document metadata
# test_doc_metadata = [
#     {
#         'doc_id': '2208-26',
#         'date': '2020-12-31',
#         'description': 'Central Bank of Sri Lanka Balance Sheet as at 30th November 2020 (Reserved)',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2020/12/2208-26_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2208-27',
#         'date': '2020-12-31',
#         'description': 'Consumer Affairs Authority - Directs for Hand Sanitizers',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2020/12/2208-27_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2208-28',
#         'date': '2020-12-15',
#         'description': 'Land Acquisition - Ulpothakumbura, Kandy Four Gravets D/S Division, Kandy District',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2020/12/2208-28_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2208-29',
#         'date': '2020-11-30',
#         'description': 'Department of Local Government - Uva Province - The meeting of the Haldummulla Pradeshiya Sabha',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2020/11/2208-29_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2208-30',
#         'date': '2020-11-15',
#         'description': 'Land Acquisition - Basnagoda, Ruwanwella D/S Division, Kegalle District',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2020/11/2208-30_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2209-01',
#         'date': '2021-01-05',
#         'description': 'Ministry of Health - COVID-19 Guidelines Update',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2021/01/2209-01_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2209-02',
#         'date': '2021-01-15',
#         'description': 'Department of Education - School Reopening Guidelines',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2021/01/2209-02_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2209-03',
#         'date': '2021-02-01',
#         'description': 'Treasury - Budget Amendment Notice',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2021/02/2209-03_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2209-04',
#         'date': '2019-12-31',
#         'description': 'Year End Financial Report 2019',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2019/12/2209-04_E.pdf',
#         'availability': 'Available'
#     },
#     {
#         'doc_id': '2209-05',
#         'date': '2019-12-01',
#         'description': 'December 2019 Policy Update',
#         'download_url': 'https://documents.gov.lk/view/extra-gazettes/2019/12/2209-05_E.pdf',
#         'availability': 'Available'
#     }
# ]

# # Test cases
# def test_filter_function():
#     print("=" * 50)
#     print("TESTING DOCUMENT METADATA FILTER FUNCTION")
#     print("=" * 50)
    
#     print(f"Total documents in test dataset: {len(test_doc_metadata)}")
#     print()
    
#     # Test 1: year-lang filtering (should return all documents)
#     print("TEST 1: year-lang filtering")
#     print("-" * 30)
#     result1 = filter_doc_metadata(test_doc_metadata, "year-lang", year="2020", month=None, date=None)
#     print(f"Result: {len(result1)} documents returned (should be all {len(test_doc_metadata)} documents)")
#     print()
    
#     # Test 2: year-month-lang filtering (December 2020)
#     print("TEST 2: year-month-lang filtering (December 2020)")
#     print("-" * 30)
#     result2 = filter_doc_metadata(test_doc_metadata, "year-month-lang", year="2020", month="12", date=None)
#     print(f"Result: {len(result2)} documents found for December 2020")
#     for doc in result2:
#         print(f"  - {doc['doc_id']}: {doc['date']} - {doc['description'][:50]}...")
#     print()
    
#     # Test 3: year-month-lang filtering (November 2020)
#     print("TEST 3: year-month-lang filtering (November 2020)")
#     print("-" * 30)
#     result3 = filter_doc_metadata(test_doc_metadata, "year-month-lang", year="2020", month="11", date=None)
#     print(f"Result: {len(result3)} documents found for November 2020")
#     for doc in result3:
#         print(f"  - {doc['doc_id']}: {doc['date']} - {doc['description'][:50]}...")
#     print()
    
#     # Test 4: year-month-day-lang filtering (December 31, 2020)
#     print("TEST 4: year-month-day-lang filtering (December 31, 2020)")
#     print("-" * 30)
#     result4 = filter_doc_metadata(test_doc_metadata, "year-month-day-lang", year="2020", month="12", date="31")
#     print(f"Result: {len(result4)} documents found for December 31, 2020")
#     for doc in result4:
#         print(f"  - {doc['doc_id']}: {doc['date']} - {doc['description'][:50]}...")
#     print()
    
#     # Test 5: year-month-day-lang filtering (January 5, 2021)
#     print("TEST 5: year-month-day-lang filtering (January 5, 2021)")
#     print("-" * 30)
#     result5 = filter_doc_metadata(test_doc_metadata, "year-month-day-lang", year="2021", month="1", date="5")
#     print(f"Result: {len(result5)} documents found for January 5, 2021")
#     for doc in result5:
#         print(f"  - {doc['doc_id']}: {doc['date']} - {doc['description'][:50]}...")
#     print()
    
#     # Test 6: No results case
#     print("TEST 6: No results case (March 2020)")
#     print("-" * 30)
#     result6 = filter_doc_metadata(test_doc_metadata, "year-month-lang", year="2020", month="3", date=None)
#     print(f"Result: {len(result6)} documents found for March 2020 (should be 0)")
#     print()
    
#     # Test 7: Single digit month/date handling
#     print("TEST 7: Single digit month/date handling (January 2021)")
#     print("-" * 30)
#     result7 = filter_doc_metadata(test_doc_metadata, "year-month-lang", year="2021", month="1", date=None)
#     print(f"Result: {len(result7)} documents found for January 2021")
#     for doc in result7:
#         print(f"  - {doc['doc_id']}: {doc['date']} - {doc['description'][:50]}...")
#     print()




# def test():
#     scrape_doc_table_metadata(
#         url="https://documents.gov.lk/view/extra-gazettes/egz_2010.html",
#         lang="en",  # or "en", "ta"
#         output_path=None
#     )

if __name__ == "__main__":
    main()
    # test()
    # test_filter_function()








# <table class="table table-bordered table-striped table-hover">
#         <thead class="table-dark">
#           <tr>
#             <th>Gazettes Number</th>
#             <th class="date-column">Date</th>
#             <th>Description</th>
#             <th>Download</th>
#           </tr>
#         </thead>
#         <tbody>
#           <tr>
#             <td>2417/14</td>
#             <td class="date-column">2024-12-31</td>
#             <td>Minister of Transport Highways Ports and Civil Aviation - Merchant Shipping Act. No.52 of 1971 Merchant Shipping (Non. Convention Vessel) Regulations No. 01 of 2024 </td>
#             <td>
#               <a href="2024/12/2417-14_E.pdf" target="_blank" rel="noopener noreferrer"><button class="btn btn-primary btn-sm">English</button></a>
#               <a href="2024/12/2417-14_S.pdf" target="_blank" rel="noopener noreferrer"><button class="btn btn-secondary btn-sm">Sinhala</button></a>
#               <a href="2024/12/2417-14_T.pdf" target="_blank" rel="noopener noreferrer"><button class="btn btn-success btn-sm">Tamil</button></a>
#             </td>
#           </tr>
#            <tr>
#             <td>2416/34</td>
#             <td class="date-column">2024-12-27</td>
#             <td>Land Title Settlement Dept. - Akbapura, Medirigiriya D/S Division, Polonnaruwa District - Cad. Map No. 120061 (24/0856)</td>
#             <td>
#               <button class="btn btn-primary btn-sm" disabled>English</button>
#               <button class="btn btn-secondary btn-sm" disabled>Sinhala</button>
#               <button class="btn btn-success btn-sm" disabled>Tamil</button>
#             </td>
#           </tr>
#           </tbody>
# </table>