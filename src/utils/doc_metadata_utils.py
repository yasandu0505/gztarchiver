import json
from typing import List, Dict

def load_doc_metadata_file(json_path: str) -> List[Dict[str, str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_doc_metadata(doc_metadata, kind, year=None, month=None, date=None):
    
    if kind == "year-lang":
        return doc_metadata
    
    elif kind == "year-month-lang":
        if not year or not month:
            print("Error: year and month required for year-month-lang filtering")
            return doc_metadata
        
        target_year_month = f"{year}-{month.zfill(2)}"
        print(f"Filtering by year-month: {target_year_month}")
        
        filtered_docs = []
        
        for doc in doc_metadata:
            doc_date = doc.get('date', '')
            if doc_date.startswith(target_year_month):  # e.g., "2020-12-31" starts with "2020-12"
                filtered_docs.append(doc)
                status = f"Document found on : {target_year_month}"
            else:
                status = f"No document found on : {target_year_month}"
        
        return filtered_docs, status
    
    elif kind == "year-month-day-lang":
        if not year or not month or not date:
            print("Error: year, month, and date required for year-month-day-lang filtering")
            return doc_metadata
        
        target_date = f"{year}-{month.zfill(2)}-{date.zfill(2)}"  # Ensure month and date are 2 digits
        print(f"Filtering by year-month-day: {target_date}")
        
        filtered_docs = []
        for doc in doc_metadata:
            doc_date = doc.get('date', '')
            if doc_date == target_date:
                filtered_docs.append(doc)
                status = f"Document found on : {target_date}"
            else:
                status = f"No document found on : {target_date}"
        
        return filtered_docs, status
    
    else:
        print(f"Unknown filter kind: {kind}")
        return doc_metadata
            
    