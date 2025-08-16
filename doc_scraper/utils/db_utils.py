from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def connect_to_db(mongo_uri):
    try:
        client = MongoClient(mongo_uri)
        
        # Attempt to connect to the server
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully.")

        return client

    except ConnectionFailure as e:
        print("❌ Failed to connect to MongoDB:", e)
        return None

def insert_docs_by_year(db, prepared_metadata_to_store, year):
    for doc in prepared_metadata_to_store:
        try:
            # Extract year from the document_date
            collection_name = f"gazettes_{year}"
            collection = db[collection_name]

            # Insert the document
            result = collection.insert_one(doc)
            print(f"📄 Inserted {doc['document_id']} into {collection_name}, ID: {result.inserted_id}")

        except Exception as e:
            print(f"❌ Failed to insert {doc['document_id']}: {e}")
    
    return

def prepare_metadata_for_db(all_download_metadata, classified_metadata_dic):
    merged_output = []
    
    for doc in all_download_metadata:
        doc_id = doc['doc_id']
        
        # Get classification data if available (only for available documents)
        classification = classified_metadata_dic.get(doc_id, {})
        
        merged_output.append({
            "document_id": doc_id,
            "description": doc['des'],
            "document_date": doc['date'],
            "document_type": classification.get('doc_type', "UNAVAILABLE"),
            "reasoning": classification.get('reasoning', "NOT-FOUND"),
            "file_path": str(doc['file_path']),
            "download_url": doc['download_url'],
            "availability": doc['availability']
        })
    
    return merged_output


