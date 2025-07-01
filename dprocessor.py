import os
from gazette_tracker.processor import find_gazette_pdf

BASE_DIR = os.path.expanduser("~/Desktop/gazette-archive")

def main():
    files = find_gazette_pdf(BASE_DIR)
    print(f"Found {len(files)} gazettes....")
    for path in files[:5]:
        print("->>>", path )

if __name__ == "__main__":
    main()