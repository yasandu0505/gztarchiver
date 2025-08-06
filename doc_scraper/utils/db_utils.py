def prepare_metadata_for_db(upload_results, classified_metadata_dic):
    
    # Merge data  
    merged_output = []
    
    upload_details = upload_results["upload_details"]
        
    # Convert to lookup dictionary by doc_id
    upload_lookup = {item["doc_id"]: item for item in upload_details}
                  
    for doc_id, classification in classified_metadata_dic.items():
        upload_info = upload_lookup.get(doc_id, {})
        merged_output.append({
            "document_id": doc_id,
            "document_date": classification.get("doc_date"),
            "document_type": classification.get("doc_type"),
            "reasoning": classification.get("reasoning"),
            "gdrive_file_id": upload_info.get("gdrive_file_id"),
            "gdrive_file_url": upload_info.get("gdrive_file_url"),
            "download_url": upload_info.get("download_url")
        })
        
    return merged_output

