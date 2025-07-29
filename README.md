# PDF Educational Software Extraction System

## Overview
This system analyzes PDF documents from school districts to extract educational software information using GPT-4 multimodal capabilities. It processes documents from the RA_tasks_2025 folder structure and generates comprehensive CSV reports.

## Files Description

### Core Analysis Scripts
- **`production_analyzer.py`** - Main production script with comprehensive error handling, logging, and progress tracking
- **`quick_test.py`** - Quick test script for validating functionality on sample files

### Execution Scripts
- **`run_complete_analysis.py`** - Execute complete analysis on ALL districts (production ready)
- **`view_results.py`** - Analyze and generate reports from extracted data
- **`main.py`** - Interactive menu interface for all operations

### Support Files
- **`multimodal_rag.py`** - Reference multimodal RAG implementation (documentation/example)
- **`.env`** - Environment variables (contains OpenAI API key)
- **`README.md`** - Complete documentation
- **`.gitignore`** - Git ignore patterns

### Data Files
- **`RA_tasks_2025/`** - Source PDF documents organized by district and round
- **`RA_tasks_2025.zip`** - Original source data archive (backup)
- **`results/`** - Output directory for generated CSV files and reports

### Removed Files (Legacy/Redundant)
The following files were removed during cleanup as they were redundant or superseded by better implementations:
- **`pdf_analyzer.py`** - Superseded by `production_analyzer.py` (had basic error handling, no logging)
- **`test_analyzer.py`** - Only tested the old pdf_analyzer.py, replaced by `quick_test.py`
- **`batch_analyzer.py`** - Limited batch processor, functionality merged into production_analyzer.py
- **`quick_test_results.csv`** - Temporary test output (regenerated as needed)
- **`processing.log`** - Log file (regenerated during analysis)

## Required Python Packages
```bash
pip install PyMuPDF python-dotenv requests pandas
```

## Folder Structure Expected
```
RA_tasks_2025/
├── District_Name/
│   ├── R1/ or Round 1/ or round 1/ (case insensitive)
│   ├── R2/ or Round 2/ or round 2/
│   ├── R3/ or Round 3/ or round 3/
│   ├── R4/ or Round 4/ or round 4/
│   └── *.pdf files in each round folder
```

Special cases handled:
- Canton district uses FY 16-17, FY 17-18, FY 18-19 naming
- Mixed case and various round naming conventions
- Missing rounds (marked as 0 in summary)

## Data Fields Extracted

### Required Fields per Specification:
1. **District** - Name of the district
2. **School_Name** - Specific school if mentioned
3. **Approx_Level** - PreK, Elementary, Middle, High, Multiple, Alt
4. **Software** - Name of the software/application
5. **Vendor** - Company providing the software
6. **Use_Type** - Administrative or Instructional
7. **Host_Type** - Cloud or Install
8. **Num_School_LIC** - Number of school-specific licenses
9. **Num_District_LIC** - Number of district-wide licenses
10. **Cost_per_LIC** - Cost per license
11. **Cost_total** - Total cost
12. **Contract_StartMonth** - Contract start month
13. **Contract_StartYear** - Contract start year
14. **Contract_Length_Years** - Contract length in years
15. **Install_Month** - Installation month
16. **Install_Year** - Installation year
17. **Quote_Month** - Quote month
18. **Quote_Year** - Quote year
19. **Misc_Notes** - Additional notes and anomalies
20. **Round** - Data collection round (1-4)

### Additional Fields Added:
21. **Source_File** - PDF filename for traceability
22. **Page_Number** - Page number within PDF

## Usage Instructions

### Quick Test (Recommended First Step)
```bash
python quick_test.py
```
Tests the system on 3 sample files to verify functionality.

### Limited Production Test
```bash
python production_analyzer.py
```
Processes first 10 districts with 5 PDFs per round (good for testing).

### Complete Production Analysis
```bash
python run_complete_analysis.py
```
Processes ALL districts and PDFs. Takes several hours to complete.

### View and Analyze Results
```bash
python view_results.py
```
Generates analysis reports and summary statistics from extracted data.

## Output Files

### Location: `results/`

### Main Output Files:
- **`extracted_software_data.csv`** - Complete detailed records
- **`district_summary.csv`** - District statistics (page counts, PDF counts, etc.)
- **`district_analysis_report.csv`** - District analysis with software counts and costs
- **`vendor_analysis_report.csv`** - Vendor analysis with market share
- **`software_popularity_report.csv`** - Software usage across districts

### Backup Files:
- **`final_detailed_results_TIMESTAMP.csv`** - Timestamped backup of detailed data
- **`final_district_summary_TIMESTAMP.csv`** - Timestamped backup of summary
- **`intermediate_*_TIMESTAMP.csv`** - Intermediate results saved every 5 districts

### Log Files:
- **`processing.log`** - Detailed processing log with errors and statistics

## System Features

### Error Handling
- Comprehensive error logging
- Graceful handling of corrupted PDFs
- API rate limiting management
- Intermediate result saving (every 5 districts)

### Data Validation
- Round number vs. year consistency checking
- JSON response validation and cleaning
- Cost data extraction and normalization
- Duplicate round folder handling

### Progress Tracking
- Real-time progress logging
- Statistics tracking (API calls, errors, records extracted)
- Intermediate saves to prevent data loss
- Detailed timing information

### GPT-4 Integration
- Multimodal analysis (image + text)
- Comprehensive extraction prompts
- Error recovery and retry logic
- Rate limiting compliance

## Processing Statistics Tracked
- Districts processed
- PDFs processed  
- Pages analyzed
- Software records extracted
- API calls made
- Errors encountered
- Processing duration

## Special Handling

### Document Types Processed:
- Organized tables with software and pricing
- Scanned contracts for educational software
- Invoice documents
- Email correspondence
- Vendor reports
- Student Data Privacy contracts

### Edge Cases Handled:
- Free software (when documented)
- Renewal subscriptions
- Multi-year contracts
- School-specific vs district-wide licenses
- Missing or incomplete information

## API Requirements
- OpenAI API key with GPT-4 access
- Sufficient API rate limits for large-scale processing
- Estimated cost: $5-$40 depending on document volume

## Performance Considerations
- Processing time: ~2-3 seconds per page
- Rate limiting: 1.5-second delays between API calls
- Memory usage: Moderate (processes one page at a time)
- Total estimated time: 3-6 hours for complete analysis

## Troubleshooting

### Common Issues:
1. **API Key Issues**: Ensure OPENAI_API_KEY is set in .env file
2. **Rate Limiting**: System includes built-in delays
3. **PDF Corruption**: Errors logged, processing continues
4. **Memory Issues**: Restart if needed, intermediate saves prevent data loss

### Recovery:
- Check `processing.log` for detailed error information
- Use intermediate files if main process interrupted
- Re-run specific districts if needed

## Data Quality Notes
- Some fields may be empty if information not available in source documents
- Cost data availability varies by district and round
- Round 3 and 4 data may be more complete due to improved data collection procedures
- Connecticut districts may show increased software usage after data privacy law changes
