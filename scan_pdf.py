from pathlib import Path
from PyPDF2 import PdfReader
import os
import re

def validate_folder_structure_and_pdfs(root_folder):
    root = Path(root_folder)
    
    if not root.exists():
        print(f"Error: Root folder '{root_folder}' does not exist.")
        return
    
    # Counters for statistics
    total_pdfs = 0
    valid_pdfs = 0
    broken_pdfs = []
    structure_issues = []
    unexpected_files = []
    empty_date_folders = 0
    date_folders_with_pdfs = 0
    total_gazette_folders = 0
    
    print(f"Validating gazette archive at: {root}")
    print("=" * 60)
    
    # Iterate through year folders
    for year_path in sorted(root.iterdir()):
        if not year_path.is_dir():
            # Check if it's an expected file type in root
            if year_path.suffix.lower() in ['.csv', '.txt']:
                print(f"Found expected file in root: {year_path.name}")
            else:
                unexpected_files.append(f"Unexpected file in root: {year_path.name}")
            continue
            
        # Validate year format (should be 4 digits)
        if not re.match(r'^\d{4}$', year_path.name):
            structure_issues.append(f"Invalid year folder format: {year_path.name}")
            continue
            
        print(f"\nProcessing year: {year_path.name}")
        
        # Check for CSV and TXT files in year folder
        year_files = [f for f in year_path.iterdir() if f.is_file()]
        csv_files = [f for f in year_files if f.suffix.lower() == '.csv']
        txt_files = [f for f in year_files if f.suffix.lower() == '.txt']
        
        if csv_files:
            print(f"  Found CSV files: {[f.name for f in csv_files]}")
        if txt_files:
            print(f"  Found TXT files: {[f.name for f in txt_files]}")
        
        # Check for unexpected files in year folder
        for file in year_files:
            if file.suffix.lower() not in ['.csv', '.txt']:
                unexpected_files.append(f"Unexpected file in {year_path.name}: {file.name}")
        
        # Iterate through month folders
        for month_path in sorted([p for p in year_path.iterdir() if p.is_dir()]):
            # Validate month format (should be 01-12)
            if not re.match(r'^(0[1-9]|1[0-2])$', month_path.name):
                structure_issues.append(f"Invalid month folder format: {year_path.name}/{month_path.name}")
                continue
                
            # Check for unexpected files in month folder
            month_files = [f for f in month_path.iterdir() if f.is_file()]
            for file in month_files:
                unexpected_files.append(f"Unexpected file in {year_path.name}/{month_path.name}: {file.name}")
                
            # Iterate through day folders
            for day_path in sorted([p for p in month_path.iterdir() if p.is_dir()]):
                # Validate day format (should be 01-31)
                if not re.match(r'^(0[1-9]|[12][0-9]|3[01])$', day_path.name):
                    structure_issues.append(f"Invalid day folder format: {year_path.name}/{month_path.name}/{day_path.name}")
                    continue
                
                # Check for unexpected files in day folder
                day_files = [f for f in day_path.iterdir() if f.is_file()]
                for file in day_files:
                    unexpected_files.append(f"Unexpected file in {year_path.name}/{month_path.name}/{day_path.name}: {file.name}")
                
                # Get gazette folders in this day
                gazette_folders = [p for p in day_path.iterdir() if p.is_dir()]
                
                if not gazette_folders:
                    # Empty date folder - this is normal
                    empty_date_folders += 1
                else:
                    # Date folder has gazette folders
                    date_folders_with_pdfs += 1
                    
                    # Iterate through gazette_id folders
                    for gazette_path in sorted(gazette_folders):
                        gazette_id = gazette_path.name
                        total_gazette_folders += 1
                        print(f"  Checking gazette: {year_path.name}/{month_path.name}/{day_path.name}/{gazette_id}")
                        
                        # Check for English PDF file
                        expected_english_pdf = gazette_path / f"{gazette_id}_english.pdf"
                        found_english_pdf = False
                        gazette_pdfs = []
                        
                        for item in gazette_path.iterdir():
                            if item.is_file() and item.suffix.lower() == '.pdf':
                                gazette_pdfs.append(item)
                                total_pdfs += 1
                                
                                # Check if this is the expected English PDF
                                if item.name == f"{gazette_id}_english.pdf":
                                    found_english_pdf = True
                                elif not re.match(f"{gazette_id}_(sinhala|tamil).pdf", item.name):
                                    # PDF with unexpected naming format
                                    structure_issues.append(f"Unexpected PDF filename: {item}")
                                    
                            elif item.is_file():
                                unexpected_files.append(f"Unexpected non-PDF file: {item}")
                            elif item.is_dir():
                                unexpected_files.append(f"Unexpected subdirectory: {item}")
                        
                        # Report if English PDF is missing
                        if not found_english_pdf:
                            structure_issues.append(f"Missing English PDF: {expected_english_pdf}")
                        
                        # Validate all PDF files found
                        for pdf_path in gazette_pdfs:
                            try:
                                with open(pdf_path, "rb") as pdf_file:
                                    PdfReader(pdf_file)
                                valid_pdfs += 1
                            except Exception as e:
                                broken_pdfs.append(f"{pdf_path} - Error: {str(e)}")
    
    # Print summary report
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"Total date folders (YYYY/MM/DD): {empty_date_folders + date_folders_with_pdfs}")
    print(f"Empty date folders: {empty_date_folders}")
    print(f"Date folders with gazettes: {date_folders_with_pdfs}")
    print(f"Total gazette folders: {total_gazette_folders}")
    print(f"Total PDF files found: {total_pdfs}")
    print(f"Valid PDFs: {valid_pdfs}")
    print(f"Broken PDFs: {len(broken_pdfs)}")
    print(f"Structure issues: {len(structure_issues)}")
    print(f"Unexpected files: {len(unexpected_files)}")
    
    # Detailed reports
    if broken_pdfs:
        print(f"\n{'BROKEN PDFs:':<25}")
        print("-" * 50)
        for pdf in broken_pdfs:
            print(f"  • {pdf}")
    
    if structure_issues:
        print(f"\n{'STRUCTURE ISSUES:':<25}")
        print("-" * 50)
        for issue in structure_issues:
            print(f"  • {issue}")
    
    if unexpected_files:
        print(f"\n{'UNEXPECTED FILES:':<25}")
        print("-" * 50)
        for unexpected in unexpected_files:
            print(f"  • {unexpected}")
    
    # Overall status
    print(f"\n{'STATUS:':<25}")
    print("-" * 50)
    if not any([broken_pdfs, structure_issues, unexpected_files]):
        print("  ✅ Archive structure and all PDFs are valid!")
    else:
        print("  ❌ Issues found in the archive. See details above.")
    
    return {
        'total_date_folders': empty_date_folders + date_folders_with_pdfs,
        'empty_date_folders': empty_date_folders,
        'date_folders_with_pdfs': date_folders_with_pdfs,
        'total_gazette_folders': total_gazette_folders,
        'total_pdfs': total_pdfs,
        'valid_pdfs': valid_pdfs,
        'broken_pdfs': len(broken_pdfs),
        'structure_issues': len(structure_issues),
        'unexpected_files': len(unexpected_files)
    }

if __name__ == "__main__":
    validate_folder_structure_and_pdfs(Path.home() / "Desktop/gazette-archive")