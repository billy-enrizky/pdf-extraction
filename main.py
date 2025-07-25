#!/usr/bin/env python3
"""
COMPLETE SOLUTION SUMMARY
Educational Software PDF Analysis System for RA_tasks_2025

This script provides a complete overview and easy access to all functionality.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def print_banner():
    print("=" * 80)
    print("EDUCATIONAL SOFTWARE PDF ANALYSIS SYSTEM")
    print("Automated extraction of software data from school district documents")
    print("=" * 80)

def check_requirements():
    """Check if all requirements are met"""
    print("\n🔍 CHECKING REQUIREMENTS...")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key found")
    else:
        print("❌ OpenAI API key not found in .env file")
        return False
    
    # Check data folder
    data_folder = Path("RA_tasks_2025")
    if data_folder.exists():
        districts = len([d for d in data_folder.iterdir() if d.is_dir() and d.name != ".DS_Store"])
        print(f"✅ Data folder found with {districts} districts")
    else:
        print("❌ RA_tasks_2025 folder not found")
        return False
    
    # Check Python packages
    try:
        import fitz
        import requests
        import pandas
        print("✅ All required Python packages installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False
    
    return True

def show_menu():
    """Show main menu options"""
    print("\n📋 AVAILABLE OPTIONS:")
    print("1. Quick Test (3 sample files) - Recommended first step")
    print("2. Limited Analysis (10 districts, 5 PDFs per round) - Good for testing") 
    print("3. Complete Analysis (ALL districts and PDFs) - Production run")
    print("4. View Results and Generate Reports")
    print("5. Check Processing Status")
    print("6. Show File Descriptions")
    print("7. Exit")

def quick_test():
    """Run quick test"""
    print("\n🚀 RUNNING QUICK TEST...")
    print("This will test the system on 3 sample PDF files.")
    
    confirm = input("Continue? (y/n): ").lower()
    if confirm == 'y':
        os.system("python quick_test.py")
    else:
        print("Quick test cancelled.")

def limited_analysis():
    """Run limited analysis"""
    print("\n🔬 RUNNING LIMITED ANALYSIS...")
    print("This will process the first 10 districts with 5 PDFs per round.")
    print("Estimated time: 30-60 minutes")
    
    confirm = input("Continue? (y/n): ").lower()
    if confirm == 'y':
        os.system("python production_analyzer.py")
    else:
        print("Limited analysis cancelled.")

def complete_analysis():
    """Run complete analysis"""
    print("\n🏭 RUNNING COMPLETE ANALYSIS...")
    print("⚠️  WARNING: This will process ALL districts and PDFs")
    print("📅 Estimated time: 3-6 hours")
    print("💰 Estimated API cost: $50-200")
    print("💾 Results will be saved automatically every 5 districts")
    
    confirm = input("Are you sure you want to proceed? (yes/no): ").lower()
    if confirm == 'yes':
        print("\nStarting complete analysis...")
        os.system("python run_complete_analysis.py")
    else:
        print("Complete analysis cancelled.")

def view_results():
    """View results and generate reports"""
    print("\n📊 VIEWING RESULTS...")
    
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ No results directory found. Run an analysis first.")
        return
    
    # Check for results files
    csv_files = list(results_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No results files found. Run an analysis first.")
        return
    
    print(f"✅ Found {len(csv_files)} results files")
    os.system("python view_results.py")

def check_status():
    """Check processing status"""
    print("\n📈 CHECKING STATUS...")
    
    # Check results directory
    results_dir = Path("results")
    if results_dir.exists():
        files = list(results_dir.glob("*.csv"))
        if files:
            latest_file = max(files, key=lambda x: x.stat().st_mtime)
            print(f"✅ Latest results file: {latest_file.name}")
            print(f"📅 Last modified: {latest_file.stat().st_mtime}")
        else:
            print("📂 Results directory exists but no CSV files found")
    else:
        print("📂 No results directory found")
    
    # Check log file
    log_file = Path("processing.log")
    if log_file.exists():
        print(f"📋 Log file exists: {log_file.stat().st_size} bytes")
        print("📄 Last 10 lines of log:")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"   {line.strip()}")
    else:
        print("📋 No log file found")

def show_file_descriptions():
    """Show descriptions of all files"""
    print("\n📁 FILE DESCRIPTIONS:")
    
    files = {
        "quick_test.py": "Quick test on 3 sample files (recommended first step)",
        "production_analyzer.py": "Production analyzer with comprehensive features",
        "run_complete_analysis.py": "Complete analysis - ALL districts and PDFs",
        "view_results.py": "Analyze results and generate reports",
        "multimodal_rag.py": "Reference multimodal RAG implementation",
        "README.md": "Complete documentation",
        ".env": "Environment variables (API key)"
    }
    
    for filename, description in files.items():
        status = "✅" if Path(f"{filename}").exists() else "❌"
        print(f"{status} {filename:<25} - {description}")

def main():
    """Main function"""
    print_banner()
    
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above.")
        return
    
    while True:
        show_menu()
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            quick_test()
        elif choice == "2":
            limited_analysis()
        elif choice == "3":
            complete_analysis()
        elif choice == "4":
            view_results()
        elif choice == "5":
            check_status()
        elif choice == "6":
            show_file_descriptions()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main()
