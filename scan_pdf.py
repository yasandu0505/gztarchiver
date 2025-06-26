from pathlib import Path
from PyPDF2 import PdfReader
import os

def count_and_validate_pdfs(root_folder):
    root = Path(root_folder)
    pdf_files = list(root.rglob("*.pdf"))

    broken = []

    for pdf in pdf_files:
        try:
            PdfReader(open(pdf, "rb"))
        except Exception:
            broken.append(pdf)

    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Valid PDFs: {len(pdf_files) - len(broken)}")
    print(f"Broken PDFs: {len(broken)}")

    if broken:
        print("\nList of broken PDFs:")
        for path in broken:
            print(f" - {path}")

if __name__ == "__main__":
    count_and_validate_pdfs(Path.home() / "Desktop/gazette-archive")
