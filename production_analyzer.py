#!/usr/bin/env python3
"""
Production PDF Analyzer for RA_tasks_2025 folder
Processes all districts and generates comprehensive CSV with educational software data
"""

import os
import csv
import base64
import json
import re
import requests
import argparse
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import fitz  # PyMuPDF
from dotenv import load_dotenv
import time
from dataclasses import dataclass
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SoftwareRecord:
    """Data class to hold extracted software information"""
    district: str = ""
    school_name: str = ""
    approx_level: str = ""
    software: str = ""
    vendor: str = ""
    use_type: str = ""
    host_type: str = ""
    num_school_lic: str = ""
    num_district_lic: str = ""
    cost_per_lic: str = ""
    cost_total: str = ""
    contract_start_month: str = ""
    contract_start_year: str = ""
    contract_length_years: str = ""
    install_month: str = ""
    install_year: str = ""
    quote_month: str = ""
    quote_year: str = ""
    misc_notes: str = ""
    round: str = ""
    source_file: str = ""
    page_number: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for CSV writing"""
        return {
            'District': self.district,
            'School_Name': self.school_name,
            'Approx_Level': self.approx_level,
            'Software': self.software,
            'Vendor': self.vendor,
            'Use_Type': self.use_type,
            'Host_Type': self.host_type,
            'Num_School_LIC': self.num_school_lic,
            'Num_District_LIC': self.num_district_lic,
            'Cost_per_LIC': self.cost_per_lic,
            'Cost_total': self.cost_total,
            'Contract_StartMonth': self.contract_start_month,
            'Contract_StartYear': self.contract_start_year,
            'Contract_Length_Years': self.contract_length_years,
            'Install_Month': self.install_month,
            'Install_Year': self.install_year,
            'Quote_Month': self.quote_month,
            'Quote_Year': self.quote_year,
            'Misc_Notes': self.misc_notes,
            'Round': self.round,
            'Source_File': self.source_file,
            'Page_Number': self.page_number
        }

class ProductionPDFAnalyzer:
    """Production-ready PDF analyzer with comprehensive error handling and progress tracking"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.base_dir = Path("RA_tasks_2025")
        self.output_dir = Path("results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Persistent tracking files
        self.processed_pdfs_file = self.output_dir / "processed_pdfs.json"
        self.main_csv_file = self.output_dir / "extracted_software_data.csv"
        self.summary_csv_file = self.output_dir / "district_summary.csv"
        
        # Load previously processed PDFs
        self.processed_pdfs: Set[str] = self.load_processed_pdfs()
        
        # Round mapping for case-insensitive matching
        self.round_patterns = {
            'r1': '1', 'round 1': '1', 'round1': '1',
            'r2': '2', 'round 2': '2', 'round2': '2', 
            'r3': '3', 'round 3': '3', 'round3': '3',
            'r4': '4', 'round 4': '4', 'round4': '4',
            'r5': '5', 'round 5': '5', 'round5': '5',
            'fy 16-17': '1', 'fy 17-18': '2', 'fy 18-19': '3'  # Special cases like Canton
        }
        
        # Year to round validation
        self.year_to_round = {
            '2015':'1','2016': '1', '2017': '1',
            '2018': '2', 
            '2019': '3',
            '2022': '4'
        }
        
        # Statistics tracking
        self.stats = {
            'districts_processed': 0,
            'pdfs_processed': 0,
            'pages_analyzed': 0,
            'software_records_extracted': 0,
            'api_calls_made': 0,
            'errors_encountered': 0
        }
        
    def load_processed_pdfs(self) -> Set[str]:
        """Load the set of previously processed PDF files"""
        try:
            if self.processed_pdfs_file.exists():
                with open(self.processed_pdfs_file, 'r') as f:
                    data = json.load(f)
                    processed_set = set(data.get('processed_pdfs', []))
                    logger.info(f"Loaded {len(processed_set)} previously processed PDFs from tracking file")
                    return processed_set
            else:
                logger.info("No previous tracking file found. Starting fresh.")
                return set()
        except Exception as e:
            logger.warning(f"Error loading processed PDFs tracking file: {e}. Starting fresh.")
            return set()
    
    def save_processed_pdfs(self):
        """Save the current set of processed PDFs to persistent storage"""
        try:
            data = {
                'processed_pdfs': list(self.processed_pdfs),
                'last_updated': datetime.now().isoformat(),
                'total_processed': len(self.processed_pdfs)
            }
            with open(self.processed_pdfs_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.processed_pdfs)} processed PDFs to tracking file")
        except Exception as e:
            logger.error(f"Error saving processed PDFs tracking file: {e}")
    
    def clear_tracking_file(self):
        """Clear the processed PDFs tracking file"""
        try:
            if self.processed_pdfs_file.exists():
                self.processed_pdfs_file.unlink()
                self.processed_pdfs = set()
                logger.info("Processed PDFs tracking file cleared. Starting fresh.")
            else:
                logger.info("No tracking file found to clear.")
        except Exception as e:
            logger.error(f"Error clearing tracking file: {e}")
    
    def show_status(self):
        """Show processing status and previously processed PDFs count"""
        logger.info(f"Processed PDFs count: {len(self.processed_pdfs)}")
        if self.processed_pdfs_file.exists():
            logger.info(f"Tracking file last updated: {self.processed_pdfs_file.stat().st_mtime}")
        else:
            logger.info("No tracking file found.")
    
    def get_pdf_identifier(self, pdf_path: Path, district: str, round_num: str) -> str:
        """Create a unique identifier for a PDF file"""
        # Use relative path from base_dir + district + round for uniqueness
        return f"{district}/{round_num}/{pdf_path.name}"
    
    def is_pdf_already_processed(self, pdf_path: Path, district: str, round_num: str) -> bool:
        """Check if a PDF has already been processed"""
        pdf_id = self.get_pdf_identifier(pdf_path, district, round_num)
        return pdf_id in self.processed_pdfs
    
    def mark_pdf_as_processed(self, pdf_path: Path, district: str, round_num: str):
        """Mark a PDF as processed"""
        pdf_id = self.get_pdf_identifier(pdf_path, district, round_num)
        self.processed_pdfs.add(pdf_id)
        
        # Save to persistent storage every 5 PDFs
        if len(self.processed_pdfs) % 5 == 0:
            self.save_processed_pdfs()
    
    def normalize_round_name(self, folder_name: str) -> Optional[str]:
        """Convert folder name to round number with special case handling"""
        folder_lower = folder_name.lower().strip()
        return self.round_patterns.get(folder_lower)
    
    def validate_round_year(self, round_num: str, year_str: str) -> bool:
        """Validate if round number matches expected year"""
        if not year_str or not round_num:
            return True  # No validation needed if missing info
            
        expected_round = self.year_to_round.get(year_str)
        if expected_round and expected_round != round_num:
            logger.warning(f"Round {round_num} doesn't match year {year_str} (expected round {expected_round})")
            return False
        return True
    
    def encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 string"""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def extract_page_content(self, pdf_path: str, page_num: int) -> Tuple[bytes, str]:
        """Extract page as image and text from PDF"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Get page as image with good quality
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("png")
            
            # Extract text
            text = page.get_text()
            
            doc.close()
            return img_bytes, text
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path} page {page_num}: {e}")
            return b"", ""
    
    def analyze_page_with_gpt(self, image_bytes: bytes, text_content: str, 
                             district: str, round_num: str, pdf_name: str, page_num: int) -> List[SoftwareRecord]:
        """
        Send page to GPT for analysis and extract software information
        
        Features automatic retry logic with:
        - Maximum 3 retry attempts for API failures
        - Exponential backoff (2s, 3s, 4.5s delays)
        - Separate handling for different error types (RequestException, JSONDecodeError, etc.)
        - Detailed logging of retry attempts
        - Returns empty list if all retries are exhausted
        """
        
        if not image_bytes:
            return []
        
        b64_image = self.encode_image_to_base64(image_bytes)
        
        # Enhanced prompt for better extraction
        prompt = f"""
You are analyzing a document from {district} school district (Round {round_num}, Page {page_num+1}) to extract educational software information.

Document: {pdf_name}
Text content: {text_content[:800]}...

TASK: Extract ALL educational software, applications, web-based services, and technology-related items from this document.

INCLUDE these types of items:
- Educational software and applications
- Learning management systems
- Administrative software for schools
- Cloud-based educational services
- Software licenses and subscriptions
- Technology contracts and renewals
- Student information systems
- Assessment platforms
- Digital curriculum tools

EXCLUDE these items:
- Physical hardware (computers, phones, printers)
- Non-technology services (maintenance, consulting)
- Office supplies and furniture

For each software item found, return a JSON object with these exact field names:

{{
  "software": "Name of software/application/service",
  "vendor": "Company providing the software",
  "school_name": "Specific school if mentioned (leave empty if district-wide)",
  "approx_level": "PreK, Elementary, Middle, High, Multiple, or Alt (if specified)",
  "use_type": "Administrative or Instructional (if specified)", 
  "host_type": "Cloud or Install (if specified)",
  "num_school_lic": "Number of school-specific licenses (numbers only)",
  "num_district_lic": "Number of district-wide licenses (numbers only)",
  "cost_per_lic": "Cost per license (numbers only, no $ symbols)",
  "cost_total": "Total cost (numbers only, no $ symbols)",
  "contract_start_month": "Month contract started (January, February, etc.)",
  "contract_start_year": "Year contract started (4-digit year)",
  "contract_length_years": "Contract length in years (numbers only)",
  "install_month": "Month software installed (January, February, etc.)",
  "install_year": "Year software installed (4-digit year)",
  "quote_month": "Month quote was given (January, February, etc.)",
  "quote_year": "Year quote was given (4-digit year)",
  "misc_notes": "Important details, renewal info, special terms, etc."
}}

EXTRACTION RULES:
1. Extract each software item separately (don't combine multiple items)
2. For tables/invoices, create one entry per line item
3. Use only information clearly stated in the document
4. Leave fields empty ("") if information is not available
5. For costs, extract only the numerical value (e.g., "1500.00" not "$1,500.00")
6. For dates, use full month names and 4-digit years
7. Include renewal subscriptions and maintenance contracts
8. If document lists software without details, still include it with available info

CRITICAL JSON FORMATTING REQUIREMENTS:
- Return ONLY a valid JSON array of objects, no other text
- Ensure all strings are properly quoted and escaped
- Do not include trailing commas
- End all strings properly with closing quotes
- If no software is found, return []
- Validate JSON format before returning

Return ONLY a valid JSON array of objects. If no software is found, return [].

Example format:
[
  {{
    "software": "Microsoft Office 365",
    "vendor": "Microsoft Corporation",
    "school_name": "",
    "approx_level": "Multiple",
    "use_type": "Administrative",
    "host_type": "Cloud",
    "num_school_lic": "",
    "num_district_lic": "500",
    "cost_per_lic": "8.25",
    "cost_total": "4125.00",
    "contract_start_month": "July",
    "contract_start_year": "2019",
    "contract_length_years": "1",
    "install_month": "",
    "install_year": "",
    "quote_month": "June",
    "quote_year": "2019",
    "misc_notes": "Annual subscription renewal"
  }}
]
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                        }
                    ]
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.0
        }
        
        # Retry logic for API calls
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API attempt {attempt + 1}/{max_retries} for {pdf_name} page {page_num+1}")
                self.stats['api_calls_made'] += 1
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=3600
                )
                response.raise_for_status()
                
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse JSON response
                try:
                    # Clean up the response
                    if content.startswith('```json'):
                        content = content.split('```json')[1].split('```')[0]
                    elif content.startswith('```'):
                        content = content.split('```')[1].split('```')[0]
                    
                    # Additional cleaning for common JSON issues
                    content = content.strip()
                    
                    # Try to parse JSON with multiple strategies
                    extracted_data = self.parse_json_with_recovery(content, pdf_name, page_num, attempt)
                    
                    # Convert to SoftwareRecord objects
                    records = []
                    for item in extracted_data:
                        # Validate and clean data
                        contract_year = str(item.get('contract_start_year', ''))
                        if contract_year and not self.validate_round_year(round_num, contract_year):
                            item['misc_notes'] = f"{item.get('misc_notes', '')} [Year-Round mismatch noted]".strip()
                        
                        record = SoftwareRecord(
                            district=district,
                            round=round_num,
                            source_file=pdf_name,
                            page_number=str(page_num + 1),
                            software=item.get('software', ''),
                            vendor=item.get('vendor', ''),
                            school_name=item.get('school_name', ''),
                            approx_level=item.get('approx_level', ''),
                            use_type=item.get('use_type', ''),
                            host_type=item.get('host_type', ''),
                            num_school_lic=str(item.get('num_school_lic', '')),
                            num_district_lic=str(item.get('num_district_lic', '')),
                            cost_per_lic=str(item.get('cost_per_lic', '')),
                            cost_total=str(item.get('cost_total', '')),
                            contract_start_month=item.get('contract_start_month', ''),
                            contract_start_year=str(item.get('contract_start_year', '')),
                            contract_length_years=str(item.get('contract_length_years', '')),
                            install_month=item.get('install_month', ''),
                            install_year=str(item.get('install_year', '')),
                            quote_month=item.get('quote_month', ''),
                            quote_year=str(item.get('quote_year', '')),
                            misc_notes=item.get('misc_notes', '')
                        )
                        records.append(record)
                    
                    self.stats['software_records_extracted'] += len(records)
                    logger.debug(f"Successfully extracted {len(records)} records on attempt {attempt + 1}")
                    return records
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error for {pdf_name} page {page_num+1} attempt {attempt + 1}: {e}")
                    logger.debug(f"Raw content: {content[:500]}...")
                    if attempt == max_retries - 1:  # Last attempt
                        self.stats['errors_encountered'] += 1
                        return []
                    continue  # Try again
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request error for {pdf_name} page {page_num+1} attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Final API request failure for {pdf_name} page {page_num+1} after {max_retries} attempts")
                    self.stats['errors_encountered'] += 1
                    return []
                else:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                    
            except Exception as e:
                logger.warning(f"Unexpected error analyzing {pdf_name} page {page_num+1} attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Final unexpected error for {pdf_name} page {page_num+1} after {max_retries} attempts")
                    self.stats['errors_encountered'] += 1
                    return []
                else:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
        
        # Should never reach here due to return statements above
        self.stats['errors_encountered'] += 1
        return []
    
    def parse_json_with_recovery(self, content: str, pdf_name: str, page_num: int, attempt: int) -> List[Dict]:
        """
        Parse JSON with multiple recovery strategies for malformed responses
        """
        # Strategy 1: Direct parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parsing failed for {pdf_name} page {page_num+1}: {e}")
        
        # Strategy 2: Try to fix common JSON issues
        try:
            # Remove any trailing commas
            fixed_content = re.sub(r',\s*([}\]])', r'\1', content)
            
            # Try to fix unterminated strings by finding the last complete object
            if '"' in fixed_content:
                # Count quotes to see if we have unmatched quotes
                quote_count = fixed_content.count('"') - fixed_content.count('\\"')
                if quote_count % 2 != 0:
                    # Find the last complete JSON object/array
                    last_complete = self.find_last_complete_json(fixed_content)
                    if last_complete:
                        return json.loads(last_complete)
            
            return json.loads(fixed_content)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON fix attempt failed for {pdf_name} page {page_num+1}: {e}")
        
        # Strategy 3: Try to extract just the array part
        try:
            # Look for array patterns
            array_match = re.search(r'\[.*\]', content, re.DOTALL)
            if array_match:
                array_content = array_match.group()
                return json.loads(array_content)
        except json.JSONDecodeError as e:
            logger.debug(f"Array extraction failed for {pdf_name} page {page_num+1}: {e}")
        
        # Strategy 4: Try to parse partial content
        try:
            # Find individual objects within the response
            objects = self.extract_json_objects(content)
            if objects:
                return objects
        except Exception as e:
            logger.debug(f"Object extraction failed for {pdf_name} page {page_num+1}: {e}")
        
        # Strategy 5: Last resort - return empty list and log the full content
        logger.warning(f"All JSON recovery strategies failed for {pdf_name} page {page_num+1} attempt {attempt+1}")
        logger.debug(f"Failed content (first 1000 chars): {content[:1000]}")
        raise json.JSONDecodeError("All recovery strategies failed", content, 0)
    
    def find_last_complete_json(self, content: str) -> Optional[str]:
        """
        Find the last complete JSON structure in malformed content
        """
        try:
            # Start from the beginning and try to find the longest valid JSON
            for i in range(len(content), 0, -1):
                test_content = content[:i]
                try:
                    json.loads(test_content)
                    return test_content
                except json.JSONDecodeError:
                    continue
            return None
        except Exception:
            return None
    
    def extract_json_objects(self, content: str) -> List[Dict]:
        """
        Extract individual JSON objects from malformed content
        """
        objects = []
        try:
            # Look for object patterns
            object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(object_pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    obj = json.loads(match)
                    if isinstance(obj, dict) and obj.get('software'):  # Basic validation
                        objects.append(obj)
                except json.JSONDecodeError:
                    continue
            
            return objects
        except Exception:
            return []
    
    def process_pdf(self, pdf_path: Path, district: str, round_num: str) -> List[SoftwareRecord]:
        """Process a single PDF file"""
        logger.info(f"Processing {pdf_path.name} from {district} Round {round_num}")
        
        if self.is_pdf_already_processed(pdf_path, district, round_num):
            logger.info(f"Skipping already processed PDF: {pdf_path.name}")
            return []
        
        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            doc.close()
            
            all_records = []
            
            # Process each page
            for page_num in range(total_pages):
                logger.debug(f"  Analyzing page {page_num + 1}/{total_pages}")
                
                image_bytes, text_content = self.extract_page_content(str(pdf_path), page_num)
                
                if image_bytes:
                    records = self.analyze_page_with_gpt(
                        image_bytes, text_content, district, round_num, pdf_path.name, page_num
                    )
                    all_records.extend(records)
                
                self.stats['pages_analyzed'] += 1
                
                # Rate limiting
                time.sleep(1.5)
            
            self.stats['pdfs_processed'] += 1
            logger.info(f"  Extracted {len(all_records)} software records from {pdf_path.name}")
            
            # Mark as processed
            self.mark_pdf_as_processed(pdf_path, district, round_num)
            return all_records
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            self.stats['errors_encountered'] += 1
            return []
    
    def get_round_folders(self, district_path: Path) -> Dict[str, Path]:
        """Get all round folders for a district"""
        round_folders = {}
        
        if not district_path.exists():
            return round_folders
        
        for item in district_path.iterdir():
            if item.is_dir():
                round_num = self.normalize_round_name(item.name)
                if round_num:
                    # Handle duplicate rounds by preferring certain naming patterns
                    if round_num in round_folders:
                        # Prefer R1, R2, etc. over "Round 1", "round 1"
                        current_name = round_folders[round_num].name
                        new_name = item.name
                        if len(new_name) < len(current_name) or new_name.startswith('R'):
                            round_folders[round_num] = item
                    else:
                        round_folders[round_num] = item
        
        return round_folders
    
    def count_pdf_pages_in_folder(self, folder_path: Path) -> int:
        """Count total pages in all PDFs in a folder and its subfolders (recursive)"""
        total_pages = 0
        
        try:
            # Use rglob to find PDFs recursively
            for pdf_file in folder_path.rglob("*.pdf"):
                try:
                    doc = fitz.open(str(pdf_file))
                    total_pages += len(doc)
                    doc.close()
                except Exception as e:
                    logger.warning(f"Error counting pages in {pdf_file}: {e}")
        except Exception as e:
            logger.error(f"Error accessing folder {folder_path}: {e}")
        
        return total_pages
    
    def get_pdfs_sorted_by_page_count(self, folder_path: Path, limit: Optional[int] = None) -> List[Path]:
        """Get PDFs sorted by page count (smallest to largest), searching recursively in all subfolders"""
        pdf_info = []
        
        try:
            # Use rglob to find PDFs recursively
            for pdf_file in folder_path.rglob("*.pdf"):
                try:
                    doc = fitz.open(str(pdf_file))
                    page_count = len(doc)
                    doc.close()
                    pdf_info.append((pdf_file, page_count))
                except Exception as e:
                    logger.warning(f"Error counting pages in {pdf_file}: {e}")
                    # Include the file with 0 pages to still process it
                    pdf_info.append((pdf_file, 0))
        except Exception as e:
            logger.error(f"Error accessing folder {folder_path}: {e}")
            return []
        
        # Sort by page count (smallest first)
        pdf_info.sort(key=lambda x: x[1])
        
        # Extract just the file paths
        sorted_pdfs = [pdf_path for pdf_path, _ in pdf_info]
        
        # Apply limit if specified
        if limit:
            sorted_pdfs = sorted_pdfs[:limit]
            logger.info(f"    Limited to {limit} smallest PDFs by page count")
        
        return sorted_pdfs
    
    def get_available_districts(self) -> List[str]:
        """Get list of all available district names"""
        district_names = []
        if self.base_dir.exists():
            for item in self.base_dir.iterdir():
                if item.is_dir() and item.name not in [".DS_Store", "__pycache__"]:
                    district_names.append(item.name)
        return sorted(district_names)
    
    def filter_districts_by_name(self, district_names: List[str], all_districts: List[Path]) -> List[Path]:
        """Filter district folders by name(s), supporting partial matches"""
        if not district_names:
            return all_districts
        
        filtered_districts = []
        available_names = [d.name for d in all_districts]
        
        for target_name in district_names:
            # First try exact match (case-insensitive)
            exact_matches = [d for d in all_districts if d.name.lower() == target_name.lower()]
            if exact_matches:
                filtered_districts.extend(exact_matches)
                continue
            
            # Then try partial match (case-insensitive)
            partial_matches = [d for d in all_districts if target_name.lower() in d.name.lower()]
            if partial_matches:
                if len(partial_matches) == 1:
                    filtered_districts.extend(partial_matches)
                    logger.info(f"Found partial match for '{target_name}': {partial_matches[0].name}")
                else:
                    logger.warning(f"Multiple partial matches for '{target_name}': {[d.name for d in partial_matches]}")
                    logger.warning("Please be more specific. Using all matches.")
                    filtered_districts.extend(partial_matches)
            else:
                logger.error(f"No district found matching '{target_name}'")
                logger.info(f"Available districts: {', '.join(available_names)}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_districts = []
        for district in filtered_districts:
            if district not in seen:
                seen.add(district)
                unique_districts.append(district)
        
        return unique_districts

    def process_all_districts(self, limit_districts: Optional[int] = None, 
                            limit_pdfs_per_round: Optional[int] = None,
                            district_names: Optional[List[str]] = None):
        """Process all districts and create comprehensive CSV"""
        start_time = datetime.now()
        logger.info(f"Starting comprehensive PDF analysis at {start_time}")
        
        all_records = []
        summary_data = []
        
        # Get all district folders
        all_district_folders = [d for d in self.base_dir.iterdir() 
                              if d.is_dir() and d.name not in [".DS_Store", "__pycache__"]]
        
        # Filter by district names if specified
        if district_names:
            district_folders = self.filter_districts_by_name(district_names, all_district_folders)
            if not district_folders:
                logger.error("No matching districts found. Exiting.")
                return
            logger.info(f"Filtering to specific districts: {[d.name for d in district_folders]}")
        else:
            district_folders = all_district_folders
        
        if limit_districts:
            district_folders = sorted(district_folders)[:limit_districts]
            logger.info(f"Processing limited set: {limit_districts} districts")
        
        logger.info(f"Found {len(district_folders)} districts to process")
        
        for district_idx, district_folder in enumerate(sorted(district_folders)):
            district_name = district_folder.name
            logger.info(f"\n=== Processing {district_idx+1}/{len(district_folders)}: {district_name} ===")
            
            # Get round folders for this district
            round_folders = self.get_round_folders(district_folder)
            
            # Initialize summary row for this district
            summary_row = {
                'District': district_name,
                'Round_1_Pages': 0,
                'Round_2_Pages': 0,
                'Round_3_Pages': 0,
                'Round_4_Pages': 0,
                'Total_Pages': 0,
                'Round_1_PDFs': 0,
                'Round_2_PDFs': 0,
                'Round_3_PDFs': 0,
                'Round_4_PDFs': 0,
                'Total_PDFs': 0,
                'Software_Records': 0
            }
            
            # Process each round
            for round_num in ['1', '2', '3', '4']:
                if round_num in round_folders:
                    folder_path = round_folders[round_num]
                    logger.info(f"  Processing Round {round_num}: {folder_path.name}")
                    
                    # Count pages and PDFs for summary
                    page_count = self.count_pdf_pages_in_folder(folder_path)
                    
                    # Get PDFs sorted by page count (smallest to largest)
                    pdf_files = self.get_pdfs_sorted_by_page_count(folder_path, limit_pdfs_per_round)
                    
                    summary_row[f'Round_{round_num}_Pages'] = page_count
                    summary_row[f'Round_{round_num}_PDFs'] = len(pdf_files)
                    summary_row['Total_Pages'] += page_count
                    summary_row['Total_PDFs'] += len(pdf_files)
                    
                    logger.info(f"    Found {len(pdf_files)} PDF files ({page_count} total pages)")
                    
                    # Process PDFs in this round
                    round_records = []
                    for pdf_file in pdf_files:
                        records = self.process_pdf(pdf_file, district_name, round_num)
                        round_records.extend(records)
                        all_records.extend(records)
                        
                        # Progress update every 10 PDFs
                        if self.stats['pdfs_processed'] % 10 == 0:
                            logger.info(f"Progress: {self.stats['pdfs_processed']} PDFs, "
                                      f"{self.stats['software_records_extracted']} records, "
                                      f"{self.stats['api_calls_made']} API calls")
                    
                    summary_row['Software_Records'] += len(round_records)
                    logger.info(f"    Extracted {len(round_records)} software records from Round {round_num}")
                    
                else:
                    logger.info(f"  No Round {round_num} folder found")
            
            summary_data.append(summary_row)
            self.stats['districts_processed'] += 1
            
            # Save intermediate results every 5 districts
            if self.stats['districts_processed'] % 5 == 0:
                self.save_intermediate_results(all_records, summary_data)
        
        # Final save
        self.save_final_results(all_records, summary_data)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"\n=== PROCESSING COMPLETE ===")
        logger.info(f"Duration: {duration}")
        logger.info(f"Districts processed: {self.stats['districts_processed']}")
        logger.info(f"PDFs processed: {self.stats['pdfs_processed']}")
        logger.info(f"Pages analyzed: {self.stats['pages_analyzed']}")
        logger.info(f"Software records extracted: {self.stats['software_records_extracted']}")
        logger.info(f"API calls made: {self.stats['api_calls_made']}")
        logger.info(f"Errors encountered: {self.stats['errors_encountered']}")
    
    def save_intermediate_results(self, records: List[SoftwareRecord], summary_data: List[Dict]):
        """Save intermediate results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed records
        detailed_file = self.output_dir / f"intermediate_detailed_{timestamp}.csv"
        self.write_detailed_csv(records, detailed_file, append_mode=False)
        
        # Save summary
        summary_file = self.output_dir / f"intermediate_summary_{timestamp}.csv"
        self.write_summary_csv(summary_data, summary_file, append_mode=False)
        
        # Also append to main files for incremental building
        self.write_detailed_csv(records, self.main_csv_file, append_mode=True)
        self.write_summary_csv(summary_data, self.summary_csv_file, append_mode=True)
        
        # Save processed PDFs tracking
        self.save_processed_pdfs()
        
        logger.info(f"Intermediate results saved: {len(records)} records, {len(summary_data)} districts")
    
    def save_final_results(self, records: List[SoftwareRecord], summary_data: List[Dict]):
        """Save final results with append functionality"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save timestamped backup files (always new files)
        detailed_file = self.output_dir / f"final_detailed_results_{timestamp}.csv"
        self.write_detailed_csv(records, detailed_file, append_mode=False)
        
        summary_file = self.output_dir / f"final_district_summary_{timestamp}.csv"
        self.write_summary_csv(summary_data, summary_file, append_mode=False)
        
        # Append to main files (or create if they don't exist)
        self.write_detailed_csv(records, self.main_csv_file, append_mode=True)
        self.write_summary_csv(summary_data, self.summary_csv_file, append_mode=True)
        
        # Save processed PDFs tracking
        self.save_processed_pdfs()
        
        logger.info(f"Final results saved to {self.output_dir}")
        logger.info(f"Main CSV files updated: {self.main_csv_file.name}, {self.summary_csv_file.name}")
        logger.info(f"Backup files created: {detailed_file.name}, {summary_file.name}")
    
    def write_detailed_csv(self, records: List[SoftwareRecord], output_path: Path, append_mode: bool = False):
        """Write all extracted software records to CSV"""
        if not records:
            logger.warning("No records to write")
            return
        
        fieldnames = [
            'District', 'School_Name', 'Approx_Level', 'Software', 'Vendor',
            'Use_Type', 'Host_Type', 'Num_School_LIC', 'Num_District_LIC',
            'Cost_per_LIC', 'Cost_total', 'Contract_StartMonth', 'Contract_StartYear',
            'Contract_Length_Years', 'Install_Month', 'Install_Year',
            'Quote_Month', 'Quote_Year', 'Misc_Notes', 'Round',
            'Source_File', 'Page_Number'
        ]
        
        # Determine if we need to write headers
        write_headers = not (append_mode and output_path.exists())
        file_mode = 'a' if append_mode and output_path.exists() else 'w'
        
        with open(output_path, file_mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if write_headers:
                writer.writeheader()
            
            for record in records:
                writer.writerow(record.to_dict())
        
        if append_mode and output_path.exists():
            logger.info(f"Appended {len(records)} records to {output_path}")
        else:
            logger.info(f"Wrote {len(records)} records to {output_path}")
    
    def write_summary_csv(self, summary_data: List[Dict], output_path: Path, append_mode: bool = False):
        """Write district summary with page counts and statistics"""
        if not summary_data:
            logger.warning("No summary data to write")
            return
            
        fieldnames = [
            'District', 
            'Round_1_Pages', 'Round_2_Pages', 'Round_3_Pages', 'Round_4_Pages', 'Total_Pages',
            'Round_1_PDFs', 'Round_2_PDFs', 'Round_3_PDFs', 'Round_4_PDFs', 'Total_PDFs',
            'Software_Records'
        ]
        
        # Determine if we need to write headers
        write_headers = not (append_mode and output_path.exists())
        file_mode = 'a' if append_mode and output_path.exists() else 'w'
        
        with open(output_path, file_mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if write_headers:
                writer.writeheader()
            
            for row in summary_data:
                writer.writerow(row)
        
        if append_mode and output_path.exists():
            logger.info(f"Appended {len(summary_data)} district summaries to {output_path}")
        else:
            logger.info(f"Wrote {len(summary_data)} district summaries to {output_path}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Production PDF Analyzer for Educational Software Data Extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all districts (limited for testing)
  python production_analyzer.py
  
  # Process specific district(s)
  python production_analyzer.py --districts "Agawam"
  python production_analyzer.py --districts "Agawam" "Canton" "Douglas"
  
  # Process districts with partial matching
  python production_analyzer.py --districts "East"  # Matches East_Granby, East_Longmeadow, etc.
  
  # List all available districts
  python production_analyzer.py --list-districts
  
  # Full production run (all districts, all PDFs)
  python production_analyzer.py --full-run
  
  # Custom limits
  python production_analyzer.py --limit-districts 5 --limit-pdfs 10
        """
    )
    
    parser.add_argument(
        '--districts', 
        nargs='+',
        help='Specific district name(s) to process. Supports partial matching.'
    )
    
    parser.add_argument(
        '--list-districts',
        action='store_true',
        help='List all available district names and exit'
    )
    
    parser.add_argument(
        '--full-run',
        action='store_true',
        help='Run full production analysis (all districts, all PDFs)'
    )
    
    parser.add_argument(
        '--limit-districts',
        type=int,
        default=3,
        help='Maximum number of districts to process (default: 3 for testing)'
    )
    
    parser.add_argument(
        '--limit-pdfs',
        type=int,
        default=10000,
        help='Maximum number of PDFs per round to process (default: 10000 for testing)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show processing status and previously processed PDFs count'
    )
    
    parser.add_argument(
        '--clear-tracking',
        action='store_true',
        help='Clear the processed PDFs tracking file to start fresh'
    )
    
    return parser.parse_args()

def main():
    """Main execution function with CLI support"""
    args = parse_arguments()
    
    try:
        analyzer = ProductionPDFAnalyzer()
        
        # Handle list districts command
        if args.list_districts:
            districts = analyzer.get_available_districts()
            print("\nAvailable Districts:")
            print("=" * 50)
            for i, district in enumerate(districts, 1):
                print(f"{i:2d}. {district}")
            print(f"\nTotal: {len(districts)} districts")
            return
        
        # Handle status command
        if args.status:
            analyzer.show_status()
            return
        
        # Handle clear tracking command
        if args.clear_tracking:
            analyzer.clear_tracking_file()
            return
        
        # Determine processing parameters
        if args.full_run:
            # Full production run
            limit_districts = None
            limit_pdfs = None
            logger.info("Running FULL PRODUCTION analysis (all districts, all PDFs)")
        else:
            # Use specified limits or defaults
            limit_districts = args.limit_districts if not args.districts else None
            limit_pdfs = args.limit_pdfs
            if args.districts:
                logger.info(f"Running analysis for specific districts: {args.districts}")
            else:
                logger.info(f"Running LIMITED analysis (max {limit_districts} districts, {limit_pdfs} PDFs per round)")
        
        # Run the analysis
        analyzer.process_all_districts(
            limit_districts=limit_districts,
            limit_pdfs_per_round=limit_pdfs,
            district_names=args.districts
        )
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
