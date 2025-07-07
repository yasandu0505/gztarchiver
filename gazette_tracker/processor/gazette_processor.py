import os
import csv

def find_gazette_pdf(base_url):
    """
    Recursively walks the given base path and finds all gazette_id_english.pdf files.
    Returns a list of full file paths.
    """
    
    gazette_file = []
    
    for dirpath, dirnames, filenames in os.walk(base_url):
        for filename in filenames:
            if filename.endswith("_english.pdf"):
                full_path = os.path.join(dirpath, filename)
                gazette_file.append(full_path)
                
    return gazette_file
    
def extract_year_and_id(pdf_path, base_url):
    """
    Given a full path to a gazette PDF and the base archive path,
    extract the year and gazette_id from the directory structure.
    """
    
    # normalize and split the path to get the year and id
    
    relative_path = os.path.relpath(pdf_path, base_url)
    parts = relative_path.split(os.sep)
    
    if len(parts) >= 5:
        year = parts[0]
        gazette_id = parts[3]
        return {"year" : year, "gazette_id" : gazette_id , "path" : pdf_path }
    else:
        return None
    
def get_meta_data(year, gazette_id, base_url):
    """
    Given a year and gazette_id, locate the year's CSV and extract metadata for that gazette_id.
    Returns the matching row as a dictionary, or None if not found.
    """
    
    csv_file = f"{year}_archive_log.csv"
    
    csv_path = os.path.join(base_url,year, csv_file)
    
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV not found for year {year}: {csv_path}")
        return None
    
    with open(csv_path, newline='', encoding='utf-8') as log_file:
        reader = csv.DictReader(log_file)
        for row in reader:
            if row.get("gazette_id") == gazette_id and row.get("status") == "SUCCESS":
                return row
            
        
    print(f"⚠️ Gazette ID '{gazette_id}' not found in {csv_path}")
    return None

def classify_gazette(description: str) -> str:
    """
    Classify a gazette entry as 'people', 'org', or 'unknown' based on its description.
    """
    desc = description.lower()

    # People-related keywords
    people_keywords = [
        "appoint", "resign", "relieve", "removal", "assume office", "prime minister",
        "minister", "state minister", "hon.", "mp", "w.e.f", "with effect from"
    ]

    # Org-related keywords
    org_keywords = [
        "assignment of subjects", "functions and duties", "duties and functions",
        "gazette extraordinary", "correction notice", "departments", "statutory",
        "institutions", "corporation", "delegate", "transfer of functions",
        "reorganization", "amend", "amendment", "subjects and functions"
    ]

    if any(k in desc for k in people_keywords) and not any(k in desc for k in org_keywords):
        return "people"
    if any(k in desc for k in org_keywords) and not any(k in desc for k in people_keywords):
        return "org"
    return "unknown"
