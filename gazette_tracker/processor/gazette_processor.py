import os

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
    

    