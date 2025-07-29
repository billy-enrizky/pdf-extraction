#!/usr/bin/env python3
"""
Count total pages in all PDF files in RA_tasks_2025 folder
"""
import fitz  # PyMuPDF
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def count_pdf_pages():
    """Count all PDF pages in RA_tasks_2025 folder"""
    base_dir = Path("RA_tasks_2025")
    
    if not base_dir.exists():
        logger.error(f"Directory {base_dir} does not exist")
        return
    
    total_pages = 0
    total_pdfs = 0
    district_stats = []
    
    # Process each district
    for district_folder in sorted(base_dir.iterdir()):
        if not district_folder.is_dir() or district_folder.name.startswith('.'):
            continue
            
        district_pages = 0
        district_pdfs = 0
        
        logger.info(f"Processing district: {district_folder.name}")
        
        # Find all PDF files recursively in the district folder
        pdf_files = list(district_folder.rglob("*.pdf"))
        
        for pdf_file in pdf_files:
            try:
                doc = fitz.open(str(pdf_file))
                page_count = len(doc)
                doc.close()
                
                district_pages += page_count
                district_pdfs += 1
                total_pages += page_count
                total_pdfs += 1
                
                logger.debug(f"  {pdf_file.name}: {page_count} pages")
                
            except Exception as e:
                logger.warning(f"  Error processing {pdf_file}: {e}")
        
        district_stats.append({
            'district': district_folder.name,
            'pdfs': district_pdfs,
            'pages': district_pages
        })
        
        logger.info(f"  {district_folder.name}: {district_pdfs} PDFs, {district_pages} pages")
    
    # Print summary
    print("\n" + "="*60)
    print("PDF PAGE COUNT SUMMARY")
    print("="*60)
    
    print(f"\nDistrict breakdown:")
    print("-" * 40)
    for stats in district_stats:
        if stats['pdfs'] > 0:
            print(f"{stats['district']:<30} {stats['pdfs']:>3} PDFs  {stats['pages']:>4} pages")
    
    print("-" * 40)
    print(f"{'TOTAL':<30} {total_pdfs:>3} PDFs  {total_pages:>4} pages")
    print("="*60)
    
    return total_pages, total_pdfs, district_stats

if __name__ == "__main__":
    count_pdf_pages()
