#!/usr/bin/env python3
"""
System Validation Script - Verifies all components are working correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_system():
    """Comprehensive system validation"""
    print("🔍 VALIDATING EDUCATIONAL SOFTWARE PDF ANALYSIS SYSTEM")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 8
    
    # Check 1: API Key
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and len(api_key) > 20:
        print("✅ OpenAI API key: CONFIGURED")
        checks_passed += 1
    else:
        print("❌ OpenAI API key: NOT FOUND")
    
    # Check 2: Source Data
    data_dir = Path("RA_tasks_2025")
    if data_dir.exists():
        districts = len([d for d in data_dir.iterdir() if d.is_dir() and d.name != ".DS_Store"])
        print(f"✅ Source data: {districts} districts found")
        checks_passed += 1
    else:
        print("❌ Source data: RA_tasks_2025 folder not found")
    
    # Check 3: Required Scripts
    required_scripts = [
        "quick_test.py",
        "production_analyzer.py", 
        "run_complete_analysis.py",
        "view_results.py",
        "main.py"
    ]
    
    script_check = True
    for script in required_scripts:
        if Path(script).exists():
            print(f"✅ Script: {script}")
        else:
            print(f"❌ Script: {script} MISSING")
            script_check = False
    
    if script_check:
        checks_passed += 1
    
    # Check 4: Python Packages
    try:
        import fitz
        import requests
        import pandas
        print("✅ Python packages: All required packages installed")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ Python packages: Missing {e}")
    
    # Check 5: Results Directory
    results_dir = Path("results")
    if not results_dir.exists():
        results_dir.mkdir()
        print("✅ Results directory: Created")
        checks_passed += 1
    else:
        print("✅ Results directory: Exists")
        checks_passed += 1
    
    # Check 6: Quick Test Functionality
    try:
        from quick_test import QuickPDFAnalyzer
        analyzer = QuickPDFAnalyzer()
        print("✅ Quick test: Import successful")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Quick test: Import failed - {e}")
    
    # Check 7: Production Analyzer
    try:
        from production_analyzer import ProductionPDFAnalyzer
        analyzer = ProductionPDFAnalyzer()
        print("✅ Production analyzer: Import successful")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Production analyzer: Import failed - {e}")
    
    # Check 8: Sample PDF Files
    sample_files = [
        "RA_tasks_2025/Agawam/R1/Infobase.pdf",
        "RA_tasks_2025/Agawam/R1/Renaissance.pdf"
    ]
    
    pdf_check = True
    for sample in sample_files:
        if Path(sample).exists():
            print(f"✅ Sample PDF: {Path(sample).name}")
        else:
            print(f"❌ Sample PDF: {Path(sample).name} not found")
            pdf_check = False
    
    if pdf_check:
        checks_passed += 1
    
    # Final Summary
    print("\n" + "=" * 60)
    print(f"VALIDATION COMPLETE: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 SYSTEM STATUS: FULLY OPERATIONAL")
        print("\n🚀 READY FOR PRODUCTION ANALYSIS!")
        print("\nNext steps:")
        print("1. Run: python quick_test.py (30 seconds)")
        print("2. Run: python production_analyzer.py (1-2 hours)")  
        print("3. Run: python run_complete_analysis.py (3-6 hours)")
        return True
    else:
        print("⚠️  SYSTEM STATUS: ISSUES DETECTED")
        print("Please fix the failed checks before proceeding.")
        return False

if __name__ == "__main__":
    validate_system()
