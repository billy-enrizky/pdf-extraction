#!/usr/bin/env python3
"""
FINAL Production Script - Complete Analysis of All Districts
Run this script to process ALL districts and PDFs in RA_tasks_2025 folder
"""

import sys
sys.path.append('/Users/billy/Documents/pdf-extraction')

from production_analyzer import ProductionPDFAnalyzer
import logging

def run_complete_analysis():
    """Run the complete analysis on all districts"""
    try:
        analyzer = ProductionPDFAnalyzer()
        
        print("="*60)
        print("STARTING COMPLETE PDF ANALYSIS")
        print("This will process ALL districts and PDFs")
        print("Estimated time: Several hours")
        print("Results will be saved to: results/")
        print("="*60)
        
        # Run complete analysis - NO LIMITS
        analyzer.process_all_districts()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE!")
        print("Check the results folder for:")
        print("- extracted_software_data.csv (detailed software records)")
        print("- district_summary.csv (district statistics)")
        print("- final_detailed_results_*.csv (timestamped backup)")
        print("- final_district_summary_*.csv (timestamped backup)")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        print("Partial results may be available in intermediate files")
    except Exception as e:
        print(f"Error during analysis: {e}")
        logging.error(f"Complete analysis error: {e}")

if __name__ == "__main__":
    run_complete_analysis()
