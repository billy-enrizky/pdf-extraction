#!/usr/bin/env python3
"""
Results Viewer - Check processing results and generate reports
"""

import csv
import pandas as pd
from pathlib import Path
import json
from collections import defaultdict

def analyze_results():
    """Analyze the extracted results and generate summary reports"""
    
    results_dir = Path("/Users/billy/Documents/pdf-extraction/results")
    
    if not results_dir.exists():
        print("Results directory not found. Run the analyzer first.")
        return
    
    # Find the most recent detailed results file
    detailed_files = list(results_dir.glob("*detailed*.csv"))
    summary_files = list(results_dir.glob("*summary*.csv"))
    
    if not detailed_files:
        print("No detailed results files found.")
        return
    
    # Use the most recent file
    detailed_file = max(detailed_files, key=lambda x: x.stat().st_mtime)
    
    print(f"Analyzing results from: {detailed_file.name}")
    
    try:
        # Read detailed results
        df = pd.read_csv(detailed_file)
        
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"Total software records: {len(df)}")
        print(f"Unique districts: {df['District'].nunique()}")
        print(f"Unique software products: {df['Software'].nunique()}")
        print(f"Unique vendors: {df['Vendor'].nunique()}")
        
        # Round distribution
        print(f"\n=== RECORDS BY ROUND ===")
        round_counts = df['Round'].value_counts().sort_index()
        for round_num, count in round_counts.items():
            print(f"Round {round_num}: {count} records")
        
        # Top districts by software count
        print(f"\n=== TOP 10 DISTRICTS BY SOFTWARE COUNT ===")
        district_counts = df['District'].value_counts().head(10)
        for district, count in district_counts.items():
            print(f"{district}: {count} software items")
        
        # Top vendors
        print(f"\n=== TOP 10 VENDORS ===")
        vendor_counts = df[df['Vendor'] != '']['Vendor'].value_counts().head(10)
        for vendor, count in vendor_counts.items():
            print(f"{vendor}: {count} software items")
        
        # Cost analysis
        print(f"\n=== COST ANALYSIS ===")
        df['Cost_total_numeric'] = pd.to_numeric(df['Cost_total'], errors='coerce')
        
        total_cost = df['Cost_total_numeric'].sum()
        records_with_cost = df['Cost_total_numeric'].notna().sum()
        
        print(f"Records with cost information: {records_with_cost} / {len(df)}")
        print(f"Total documented costs: ${total_cost:,.2f}")
        
        if records_with_cost > 0:
            avg_cost = df['Cost_total_numeric'].mean()
            median_cost = df['Cost_total_numeric'].median()
            max_cost = df['Cost_total_numeric'].max()
            
            print(f"Average cost per software: ${avg_cost:,.2f}")
            print(f"Median cost per software: ${median_cost:,.2f}")
            print(f"Maximum cost: ${max_cost:,.2f}")
        
        # Use type analysis
        print(f"\n=== SOFTWARE USE TYPES ===")
        use_type_counts = df[df['Use_Type'] != '']['Use_Type'].value_counts()
        for use_type, count in use_type_counts.items():
            print(f"{use_type}: {count} software items")
        
        # Host type analysis  
        print(f"\n=== HOSTING TYPES ===")
        host_type_counts = df[df['Host_Type'] != '']['Host_Type'].value_counts()
        for host_type, count in host_type_counts.items():
            print(f"{host_type}: {count} software items")
        
        # Generate district report
        print(f"\n=== GENERATING DISTRICT REPORT ===")
        district_report = df.groupby('District').agg({
            'Software': 'count',
            'Vendor': 'nunique',
            'Cost_total_numeric': ['sum', 'count'],
            'Round': lambda x: list(x.unique())
        }).round(2)
        
        district_report.columns = ['Software_Count', 'Unique_Vendors', 'Total_Cost', 'Records_with_Cost', 'Rounds']
        district_report = district_report.sort_values('Software_Count', ascending=False)
        
        district_report_file = results_dir / "district_analysis_report.csv"
        district_report.to_csv(district_report_file)
        print(f"District analysis saved to: {district_report_file}")
        
        # Generate vendor report
        print(f"\n=== GENERATING VENDOR REPORT ===")
        vendor_report = df[df['Vendor'] != ''].groupby('Vendor').agg({
            'Software': 'count',
            'District': 'nunique',
            'Cost_total_numeric': ['sum', 'count'],
            'Round': lambda x: list(x.unique())
        }).round(2)
        
        vendor_report.columns = ['Software_Count', 'Districts_Served', 'Total_Revenue', 'Records_with_Cost', 'Rounds']
        vendor_report = vendor_report.sort_values('Software_Count', ascending=False)
        
        vendor_report_file = results_dir / "vendor_analysis_report.csv"
        vendor_report.to_csv(vendor_report_file)
        print(f"Vendor analysis saved to: {vendor_report_file}")
        
        # Software popularity report
        print(f"\n=== GENERATING SOFTWARE POPULARITY REPORT ===")
        software_report = df[df['Software'] != ''].groupby('Software').agg({
            'District': 'nunique',
            'Vendor': 'first',
            'Cost_total_numeric': ['sum', 'mean', 'count'],
            'Round': lambda x: list(x.unique())
        }).round(2)
        
        software_report.columns = ['Districts_Using', 'Primary_Vendor', 'Total_Cost', 'Avg_Cost', 'Records_with_Cost', 'Rounds']
        software_report = software_report.sort_values('Districts_Using', ascending=False)
        
        software_report_file = results_dir / "software_popularity_report.csv"
        software_report.to_csv(software_report_file)
        print(f"Software popularity report saved to: {software_report_file}")
        
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"All reports saved to: {results_dir}")
        
    except Exception as e:
        print(f"Error analyzing results: {e}")
        import traceback
        traceback.print_exc()

def view_sample_records(n=10):
    """View sample records from the results"""
    
    results_dir = Path("/Users/billy/Documents/pdf-extraction/results")
    detailed_files = list(results_dir.glob("*detailed*.csv"))
    
    if not detailed_files:
        print("No results files found.")
        return
    
    detailed_file = max(detailed_files, key=lambda x: x.stat().st_mtime)
    
    try:
        df = pd.read_csv(detailed_file)
        
        print(f"\n=== SAMPLE RECORDS (first {n}) ===")
        print(df.head(n).to_string(index=False))
        
        print(f"\n=== RANDOM SAMPLE ({n} records) ===") 
        print(df.sample(min(n, len(df))).to_string(index=False))
        
    except Exception as e:
        print(f"Error viewing sample records: {e}")

def main():
    """Main function with menu options"""
    
    print("="*50)
    print("PDF ANALYSIS RESULTS VIEWER")
    print("="*50)
    print("1. Analyze results and generate reports")
    print("2. View sample records")
    print("3. View both")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        analyze_results()
    elif choice == "2":
        view_sample_records()
    elif choice == "3":
        analyze_results()
        view_sample_records()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
