import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import pandas as pd
import os
import time
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import json
from pathlib import Path


def create_folder_structure_on_cloud(service, filtered_doc_metadata, archive_location, parent_folder_id=None):
    """
    Create folder structure in Google Drive similar to local structure
    Structure: parent_folder/YYYY/MM/DD/doc_id/
    
    Args:
        service: Google Drive API service object
        filtered_doc_metadata: List of document metadata
        parent_folder_id: Parent folder ID in Google Drive (None for root)
    
    Returns:
        List of upload metadata with Google Drive folder IDs
    """
    
    all_upload_metadata = []
    folder_cache = {}  # Cache folder IDs to avoid duplicate API calls
    
    base_path = Path(archive_location).expanduser()
    
    print(f"📁 Creating Google Drive folder structure for {len(filtered_doc_metadata)} documents...")
    
    for doc in filtered_doc_metadata:
        doc_id = doc.get("doc_id")
        date_str = doc.get("date")
        url = doc.get("download_url")
        availability = doc.get("availability")
        
        
        # Parse date into year/month/day
        try:
            year, month, day = date_str.split("-")
        except ValueError:
            print(f"⚠️ Skipping invalid date: {date_str}")
            continue
        
        # Create nested folder structure: YYYY/MM/DD/doc_id/
        try:
            doc_folder_id = create_nested_folders(
                service, 
                parent_folder_id, 
                [year, month, day, doc_id], 
                folder_cache
            )
        except Exception as e:
            print(f"❌ Failed to create folder structure for {doc_id}: {e}")
            continue
        
        # Determine language from URL
        if "_E.pdf" in url:
            lang_suffix = "english"
        elif "_S.pdf" in url:
            lang_suffix = "sinhala"
        elif "_T.pdf" in url:
            lang_suffix = "tamil"
        elif "N/A" in url:
            lang_suffix = "unavailable"
        else:
            lang_suffix = "unknown"
        
        if lang_suffix == "unavailable":
            file_name = "unavailable.json"
        else:
            file_name = f"{doc_id}_{lang_suffix}.pdf"
                        
        folder_path = f"{year}/{month}/{day}/{doc_id}"
        local_path = base_path / year / month / day / doc_id / file_name
        
        upload_metadata = {
            "doc_id": doc_id,
            "download_url": url,
            "file_name": file_name,
            "gdrive_folder_id": doc_folder_id,
            "gdrive_folder_path": folder_path,
            "availability": availability,
            "local_path": local_path
        }
        
        all_upload_metadata.append(upload_metadata)
        
        # Handle unavailable documents
        if availability != "Available" or url == "N/A":
            try:
                upload_unavailable_metadata(service, doc, doc_folder_id, doc_id)
                print(f"📄 File created: {folder_path} | Unavailable metadata uploaded for: {doc_id}")
            except Exception as e:
                print(f"❌ Failed to upload unavailable metadata for {doc_id}: {e}")
            continue
        
        print(f"📁 Folder created: {folder_path} (ID: {doc_folder_id})")
    
    print(f"✅ Folder structure creation completed. {len(all_upload_metadata)} items ready for upload.")
    return all_upload_metadata


def create_nested_folders(service, parent_folder_id, folder_names, folder_cache):
    """
    Create nested folders in Google Drive
    
    Args:
        service: Google Drive API service object
        parent_folder_id: Parent folder ID (None for root)
        folder_names: List of folder names to create (e.g., ['2024', '01', '15', 'doc-123'])
        folder_cache: Dict to cache folder IDs
    
    Returns:
        Final folder ID of the deepest nested folder
    """
    
    current_parent_id = parent_folder_id
    current_path = ""
    
    for folder_name in folder_names:
        current_path = f"{current_path}/{folder_name}" if current_path else folder_name
        cache_key = f"{current_parent_id}:{current_path}"
        
        # Check if folder already exists in cache
        if cache_key in folder_cache:
            current_parent_id = folder_cache[cache_key]
            continue
        
        # Check if folder exists in Google Drive
        existing_folder_id = find_folder_by_name(service, folder_name, current_parent_id)
        
        if existing_folder_id:
            # Folder exists, use it
            current_parent_id = existing_folder_id
            folder_cache[cache_key] = existing_folder_id
        else:
            # Create new folder
            try:
                new_folder_id = create_folder(service, folder_name, current_parent_id)
                current_parent_id = new_folder_id
                folder_cache[cache_key] = new_folder_id
                time.sleep(0.1)  # Small delay to avoid hitting API limits
            except Exception as e:
                print(f"❌ Failed to create folder '{folder_name}': {e}")
                raise
    
    return current_parent_id


def find_folder_by_name(service, folder_name, parent_id):
    """
    Find a folder by name within a parent folder
    
    Args:
        service: Google Drive API service object
        folder_name: Name of the folder to find
        parent_id: Parent folder ID (None for root)
    
    Returns:
        Folder ID if found, None otherwise
    """
    
    try:
        # Build query to find folder
        if parent_id:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        else:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None
        
    except HttpError as e:
        print(f"❌ Error finding folder '{folder_name}': {e}")
        return None


def create_folder(service, folder_name, parent_id):
    """
    Create a new folder in Google Drive
    
    Args:
        service: Google Drive API service object
        folder_name: Name of the folder to create
        parent_id: Parent folder ID (None for root)
    
    Returns:
        ID of the created folder
    """
    
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        folder_metadata['parents'] = [parent_id]
    
    try:
        folder = service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
        
    except HttpError as e:
        print(f"❌ Error creating folder '{folder_name}': {e}")
        raise


def upload_unavailable_metadata(service, doc_metadata, folder_id, doc_id):
    """
    Upload unavailable document metadata as a JSON file to Google Drive
    
    Args:
        service: Google Drive API service object
        doc_metadata: Document metadata dict
        folder_id: Google Drive folder ID where to upload
        doc_id: Document ID for filename
    """
    
    from googleapiclient.http import MediaInMemoryUpload
    
    # Create JSON content
    json_content = json.dumps(doc_metadata, ensure_ascii=False, indent=2)
    
    # Create media upload
    media = MediaInMemoryUpload(
        json_content.encode('utf-8'),
        mimetype='application/json'
    )
    
    # File metadata
    file_metadata = {
        'name': 'unavailable.json',
        'parents': [folder_id]
    }
    
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
        
    except HttpError as e:
        print(f"❌ Error uploading unavailable metadata: {e}")
        raise


# Example usage:
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Setup Google Drive API service
service = build('drive', 'v3', credentials=your_credentials)

# Your filtered document metadata
filtered_docs = [
    {
        "doc_id": "1234-56",
        "date": "2024-01-15",
        "download_url": "https://example.com/doc_1234-56_E.pdf",
        "availability": "Available"
    },
    # ... more documents
]

# Create folder structure (None for root, or specify a parent folder ID)
upload_metadata = create_gdrive_folder_structure(service, filtered_docs, parent_folder_id=None)

# The upload_metadata will contain Google Drive folder IDs for each document
for item in upload_metadata:
    print(f"Doc: {item['doc_id']} -> Folder ID: {item['gdrive_folder_id']}")
"""

def upload_local_documents_to_gdrive(service, upload_metadata, archived_csv_path, max_retries=3, delay_between_uploads=1):
    """
    Upload locally downloaded documents to Google Drive using archived.csv file
    
    Args:
        service: Google Drive API service object
        upload_metadata: List of upload metadata from create_folder_structure_on_cloud()
        archived_csv_path: Path to the archived.csv file containing local file paths
        max_retries: Maximum number of retry attempts for failed uploads
        delay_between_uploads: Delay in seconds between uploads to avoid rate limits
    
    Returns:
        Dict with upload statistics and results
    """
    
    upload_results = {
        "total_documents": len(upload_metadata),
        "successful_uploads": 0,
        "failed_uploads": 0,
        "unavailable_documents": 0,
        "skipped_documents": 0,
        "file_not_found": 0,
        "upload_details": [],
        "errors": []
    }
    
    print(f"🚀 Starting local document upload process for {len(upload_metadata)} items...")
    print(f"📂 Reading archived.csv from: {archived_csv_path}")
    
    # Load the archived CSV file
    try:
        archived_df = pd.read_csv(archived_csv_path)
        print(f"✅ Loaded {len(archived_df)} records from archived.csv")
    except Exception as e:
        print(f"❌ Failed to read archived.csv: {e}")
        return upload_results
    
    # Create a mapping from doc_id to file_path for quick lookup
    file_path_mapping = {}
    for _, row in archived_df.iterrows():
        doc_id = str(row.get('doc_id', '')).strip()
        file_path = str(row.get('file_path', '')).strip()
        if doc_id and file_path and file_path != 'nan':
            file_path_mapping[doc_id] = file_path
    
    print(f"📋 Created file path mapping for {len(file_path_mapping)} documents")
    
    for i, item in enumerate(upload_metadata, 1):
        doc_id = item.get("doc_id")
        file_name = item.get("file_name")
        gdrive_folder_id = item.get("gdrive_folder_id")
        folder_path = item.get("gdrive_folder_path")
        availability = item.get("availability")
        
        print(f"\n📄 Processing ({i}/{len(upload_metadata)}): {doc_id}")
        print(f"   📁 Folder: {folder_path}")
        
        # Skip unavailable documents
        if availability != "Available":
            print(f"   ⚠️ Skipping unavailable document: {doc_id}")
            upload_results["unavailable_documents"] += 1
            upload_results["upload_details"].append({
                "doc_id": doc_id,
                "status": "unavailable",
                "folder_path": folder_path,
                "file_name": file_name
            })
            continue
        
        # Check if file already exists in the folder
        if file_exists_in_folder(service, file_name, gdrive_folder_id):
            print(f"   ✅ File already exists, skipping: {file_name}")
            upload_results["skipped_documents"] += 1
            upload_results["upload_details"].append({
                "doc_id": doc_id,
                "status": "already_exists",
                "folder_path": folder_path,
                "file_name": file_name
            })
            continue
        
        # Find local file path
        if doc_id not in file_path_mapping:
            print(f"   ❌ No file path found in archived.csv for: {doc_id}")
            upload_results["file_not_found"] += 1
            upload_results["errors"].append({
                "doc_id": doc_id,
                "error": "File path not found in archived.csv",
                "folder_path": folder_path
            })
            upload_results["upload_details"].append({
                "doc_id": doc_id,
                "status": "file_not_found",
                "error": "File path not found in archived.csv",
                "folder_path": folder_path,
                "file_name": file_name
            })
            continue
        
        local_file_path = file_path_mapping[doc_id]
        
        # Check if local file exists
        if not os.path.exists(local_file_path):
            print(f"   ❌ Local file not found: {local_file_path}")
            upload_results["file_not_found"] += 1
            upload_results["errors"].append({
                "doc_id": doc_id,
                "error": f"Local file not found: {local_file_path}",
                "folder_path": folder_path
            })
            upload_results["upload_details"].append({
                "doc_id": doc_id,
                "status": "local_file_not_found",
                "error": f"Local file not found: {local_file_path}",
                "folder_path": folder_path,
                "file_name": file_name,
                "local_file_path": local_file_path
            })
            continue
        
        # Get file size for logging
        file_size = os.path.getsize(local_file_path)
        print(f"   📄 Local file: {local_file_path} ({file_size:,} bytes)")
        
        # Attempt to upload the document
        success = False
        for attempt in range(max_retries):
            try:
                # Upload to Google Drive
                print(f"   ⬆️ Uploading to Google Drive: {file_name}")
                file_id = upload_local_pdf_to_gdrive(
                    service, 
                    local_file_path, 
                    file_name, 
                    gdrive_folder_id
                )
                
                if file_id:
                    print(f"   ✅ Upload successful! File ID: {file_id}")
                    upload_results["successful_uploads"] += 1
                    upload_results["upload_details"].append({
                        "doc_id": doc_id,
                        "status": "success",
                        "gdrive_file_id": file_id,
                        "folder_path": folder_path,
                        "file_name": file_name,
                        "local_file_path": local_file_path,
                        "file_size_bytes": file_size
                    })
                    success = True
                    break
                else:
                    raise Exception("Upload returned None file ID")
                    
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed for {doc_id}: {str(e)}"
                print(f"   ❌ {error_msg}")
                
                if attempt == max_retries - 1:  # Last attempt
                    upload_results["failed_uploads"] += 1
                    upload_results["errors"].append({
                        "doc_id": doc_id,
                        "error": str(e),
                        "local_file_path": local_file_path,
                        "folder_path": folder_path
                    })
                    upload_results["upload_details"].append({
                        "doc_id": doc_id,
                        "status": "failed",
                        "error": str(e),
                        "folder_path": folder_path,
                        "file_name": file_name,
                        "local_file_path": local_file_path
                    })
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # Add delay between uploads to avoid rate limiting
        if success and delay_between_uploads > 0:
            time.sleep(delay_between_uploads)
    
    # Print summary
    print_upload_summary(upload_results)
    
    return upload_results


def upload_local_pdf_to_gdrive(service, local_file_path, file_name, folder_id):
    """
    Upload a local PDF file to Google Drive
    
    Args:
        service: Google Drive API service object
        local_file_path: Path to the local PDF file
        file_name: Name for the file in Google Drive
        folder_id: Google Drive folder ID
    
    Returns:
        File ID if successful, None otherwise
    """
    
    try:
        # Create media upload from local file
        media = MediaFileUpload(
            local_file_path,
            mimetype='application/pdf',
            resumable=True  # Use resumable upload for larger files
        )
        
        # File metadata
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file.get('id')
        
    except HttpError as e:
        print(f"   ❌ Google Drive upload error: {e}")
        raise
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        raise


def file_exists_in_folder(service, file_name, folder_id):
    """
    Check if a file with the given name already exists in the folder
    
    Args:
        service: Google Drive API service object
        file_name: Name of the file to check
        folder_id: Google Drive folder ID
    
    Returns:
        True if file exists, False otherwise
    """
    
    try:
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        return len(files) > 0
        
    except HttpError as e:
        print(f"   ⚠️ Error checking file existence: {e}")
        return False


def print_upload_summary(upload_results):
    """
    Print a summary of the upload results
    
    Args:
        upload_results: Results dictionary from upload_local_documents_to_gdrive()
    """
    
    print("\n" + "="*60)
    print("📊 UPLOAD SUMMARY")
    print("="*60)
    print(f"📄 Total documents processed: {upload_results['total_documents']}")
    print(f"✅ Successful uploads: {upload_results['successful_uploads']}")
    print(f"⚠️ Skipped (already exist): {upload_results['skipped_documents']}")
    print(f"📝 Unavailable documents: {upload_results['unavailable_documents']}")
    print(f"📁 File not found: {upload_results['file_not_found']}")
    print(f"❌ Failed uploads: {upload_results['failed_uploads']}")
    
    # Calculate total file size uploaded
    total_size = sum(
        detail.get('file_size_bytes', 0) 
        for detail in upload_results['upload_details'] 
        if detail['status'] == 'success'
    )
    
    if total_size > 0:
        print(f"📊 Total data uploaded: {format_file_size(total_size)}")
    
    if upload_results['errors']:
        print(f"\n❌ Failed Documents:")
        for error in upload_results['errors']:
            print(f"   • {error['doc_id']}: {error['error']}")
    
    print("="*60)


def format_file_size(size_bytes):
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def save_upload_results(upload_results, filename="upload_results.json"):
    """
    Save upload results to a JSON file
    
    Args:
        upload_results: Results dictionary from upload_local_documents_to_gdrive()
        filename: Output filename
    """
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(upload_results, f, ensure_ascii=False, indent=2)
        print(f"📝 Upload results saved to: {filename}")
    except Exception as e:
        print(f"⚠️ Failed to save results: {e}")


def find_archived_csv_files(base_path):
    """
    Find all archived.csv files in year folders
    
    Args:
        base_path: Base path to search for archived.csv files
    
    Returns:
        List of paths to archived.csv files
    """
    
    archived_files = []
    base_path = Path(base_path)
    
    try:
        # Look for year folders (e.g., 2010, 2011, etc.)
        for year_folder in base_path.iterdir():
            if year_folder.is_dir() and year_folder.name.isdigit():
                archived_csv = year_folder / "archived.csv"
                if archived_csv.exists():
                    archived_files.append(str(archived_csv))
                    print(f"📂 Found archived.csv: {archived_csv}")
    
    except Exception as e:
        print(f"❌ Error searching for archived.csv files: {e}")
    
    return archived_files


# Example usage:
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Setup Google Drive API service
service = build('drive', 'v3', credentials=your_credentials)

# Get upload metadata from folder creation
upload_metadata = create_folder_structure_on_cloud(
    service, 
    filtered_doc_metadata, 
    parent_folder_id="1gAb9u5B3d_ifUOhBuBQbv_lb5Qu18yF7"
)

# Upload documents from local files
results = upload_local_documents_to_gdrive(
    service, 
    upload_metadata,
    archived_csv_path="/Users/yasandu/Desktop/doc-archive/2010/archived.csv",
    max_retries=3,
    delay_between_uploads=1
)

# Or process multiple years
base_archive_path = "/Users/yasandu/Desktop/doc-archive"
archived_csv_files = find_archived_csv_files(base_archive_path)

for csv_file in archived_csv_files:
    year = Path(csv_file).parent.name
    print(f"\n🗓️ Processing year: {year}")
    
    # Filter metadata for this year
    year_metadata = [
        item for item in upload_metadata 
        if item['gdrive_folder_path'].startswith(year)
    ]
    
    if year_metadata:
        results = upload_local_documents_to_gdrive(
            service, 
            year_metadata,
            csv_file,
            max_retries=3,
            delay_between_uploads=1
        )
        
        # Save results for each year
        save_upload_results(results, f"upload_results_{year}.json")

# Save overall results
save_upload_results(results, "upload_results_all.json")
"""