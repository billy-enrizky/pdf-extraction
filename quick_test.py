#!/usr/bin/env python3
"""
Quick Test PDF Analyzer - processes just a few files to verify functionality
"""

import os
import csv
import base64
import json
import requests
import time
from pathlib import Path
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QuickPDFAnalyzer:
    """Quick analyzer for testing"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def analyze_pdf_page(self, pdf_path: str, page_num: int, district: str, round_num: str):
        """Analyze a single page"""
        try:
            # Extract page as image
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Smaller for speed
            img_bytes = pix.tobytes("png")
            text = page.get_text()
            doc.close()
            
            # Encode image
            b64_image = base64.b64encode(img_bytes).decode('utf-8')
            
            # Simple prompt for quick testing
            prompt = f"""
Analyze this document from {district} school district (Round {round_num}) and extract educational software information.

Text content: {text[:500]}...

Return a JSON array of software/technology items found. For each item, include:
- software: name of software
- vendor: vendor name  
- cost_total: total cost if mentioned
- misc_notes: any important details

Example: [{{"software": "Microsoft Office", "vendor": "Microsoft", "cost_total": "1000", "misc_notes": "Annual license"}}]

Return only valid JSON array, no other text:
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
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean and parse JSON
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0]
                elif content.startswith('```'):
                    content = content.split('```')[1].split('```')[0]
                
                try:
                    extracted_data = json.loads(content)
                    return extracted_data
                except json.JSONDecodeError:
                    print(f"JSON parse error: {content[:200]}...")
                    return []
            else:
                print(f"API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error analyzing page: {e}")
            return []

def quick_test():
    """Quick test on a few files"""
    analyzer = QuickPDFAnalyzer()
    
    # Test files
    test_files = [
        "RA_tasks_2025/Agawam/R1/Infobase.pdf",
        "RA_tasks_2025/Agawam/R1/Renaissance.pdf",
        "RA_tasks_2025/Ashford/Round 2/RepQuote153500.5 - ROUND 2.pdf"
    ]
    
    all_results = []
    
    for test_file in test_files:
        path = Path(test_file)
        if path.exists():
            print(f"\nAnalyzing: {path.name}")
            
            # Get district and round from path
            parts = path.parts
            district = parts[-3]  # District folder
            round_folder = parts[-2]  # Round folder
            
            # Normalize round
            round_num = "1"
            if "2" in round_folder.lower():
                round_num = "2"
            elif "3" in round_folder.lower():
                round_num = "3"
            elif "4" in round_folder.lower():
                round_num = "4"
            
            try:
                doc = fitz.open(str(path))
                total_pages = len(doc)
                doc.close()
                
                print(f"  District: {district}, Round: {round_num}, Pages: {total_pages}")
                
                # Analyze first page only
                results = analyzer.analyze_pdf_page(str(path), 0, district, round_num)
                
                print(f"  Found {len(results)} software items:")
                for item in results:
                    print(f"    - {item.get('software', 'Unknown')}: {item.get('vendor', 'Unknown vendor')} (${item.get('cost_total', 'N/A')})")
                
                # Add to results
                for item in results:
                    item['district'] = district
                    item['round'] = round_num
                    item['source_file'] = path.name
                    all_results.append(item)
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print(f"File not found: {test_file}")
    
    # Save results
    if all_results:
        output_file = "quick_test_results.csv"
        
        fieldnames = ['district', 'round', 'source_file', 'software', 'vendor', 'cost_total', 'misc_notes']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in all_results:
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"\nResults saved to: {output_file}")
        print(f"Total items extracted: {len(all_results)}")

if __name__ == "__main__":
    quick_test()
