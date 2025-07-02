import os
from gazette_tracker.processor import find_gazette_pdf, extract_year_and_id, get_meta_data


BASE_DIR = os.path.expanduser("~/Desktop/gazette-archive")

def main():
    files = find_gazette_pdf(BASE_DIR)
    print("\n")
    print(len(files), "entries found ...\n")
    for path in files[:50]:
        meta = extract_year_and_id(path, BASE_DIR)
        if meta:
            meta_data = get_meta_data(meta["year"], meta["gazette_id"], BASE_DIR)
            if meta_data:
                meta.update(meta_data)
            
            print(meta)
            print("\n")
            
            

if __name__ == "__main__":
    main()