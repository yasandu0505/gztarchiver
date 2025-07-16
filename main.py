from src.cmd import parse_args, identify_input_kind
from pathlib import Path
import yaml
import sys
from src.utils import load_years_metadata, get_year_link, hide_logs
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
    process.crawl(DocMetadataSpider, url=year_url, lang=str(args.lang), output_path=None)
 
    # Srat crawling
    process.start()
    
    
    
    # : Call the correct spider/downloader here based on input kind   
    




# def test():
#     scrape_doc_table_metadata(
#         url="https://documents.gov.lk/view/extra-gazettes/egz_2010.html",
#         lang="en",  # or "en", "ta"
#         output_path=None
#     )

if __name__ == "__main__":
    main()
    # test()









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