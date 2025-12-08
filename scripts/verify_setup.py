#!/usr/bin/env python3
"""
Setup verification script for GitHub Repository Evaluator
Run this to check if your environment is configured correctly
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking dependencies...")
    required = [
        'dotenv',
        'git',
        'github',
        'google.generativeai',
        'googleapiclient',
        'google.oauth2'
    ]
    
    all_installed = True
    for package in required:
        try:
            __import__(package.replace('.', '_') if '.' in package else package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Run: pip install -r requirements.txt")
            all_installed = False
    
    return all_installed

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n🔍 Checking .env file...")
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print("   ❌ .env file not found")
        print("   → Run: cp .env.example .env")
        return False
    
    print("   ✅ .env file exists")
    
    # Load and check required variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'GEMINI_API_KEY': 'Get from https://makersuite.google.com/app/apikey',
        'SPREADSHEET_ID': 'From your Google Sheet URL',
    }
    
    all_set = True
    for var, hint in required_vars.items():
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"   ✅ {var} is set")
        else:
            print(f"    {var} not set - {hint}")
            all_set = False
    
    # Optional but recommended
    optional_vars = {
        'GITHUB_TOKEN': 'Optional but recommended for detailed commit analysis'
    }
    
    for var, hint in optional_vars.items():
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}':
            print(f"   ✅ {var} is set")
        else:
            print(f"   ℹ️  {var} not set - {hint}")
    
    return all_set

def check_service_account():
    """Check if service account file exists"""
    print("\n🔍 Checking Google Service Account...")
    from src.config import Config
    
    service_account_path = Path(Config.SERVICE_ACCOUNT_FILE)
    
    if not service_account_path.exists():
        print(f"   ❌ Service account file not found: {Config.SERVICE_ACCOUNT_FILE}")
        print("   → Download from Google Cloud Console")
        print("   → Save as credentials/service_account.json")
        return False
    
    print(f"   ✅ Service account file exists")
    
    # Try to load it
    try:
        import json
        with open(service_account_path) as f:
            data = json.load(f)
            email = data.get('client_email', 'N/A')
            print(f"   ✅ Service account email: {email}")
            print(f"   → Share your Google Sheet with this email!")
    except Exception as e:
        print(f"   ⚠️  Could not read service account file: {e}")
        return False
    
    return True

def check_directories():
    """Check if required directories exist"""
    print("\n🔍 Checking directories...")
    from src.config import Config
    
    directories = {
        'credentials': Config.CREDENTIALS_DIR,
        'logs': Config.LOGS_DIR,
        'cloned_repos': Path(Config.CLONE_DIR)
    }
    
    for name, path in directories.items():
        if path.exists():
            print(f"   ✅ {name}/ exists")
        else:
            print(f"   ℹ️  {name}/ will be created automatically")
    
    return True

def test_gemini_connection():
    """Test Gemini API connection"""
    print("\n🔍 Testing Gemini API connection...")
    
    try:
        from src.config import Config
        import google.generativeai as genai
        
        if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your_gemini_api_key_here':
            print("   ⚠️  GEMINI_API_KEY not configured - skipping test")
            return False
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        response = model.generate_content("Say 'Hello' if you can receive this.")
        print(f"   ✅ Gemini API connection successful!")
        print(f"   Response: {response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ Gemini API test failed: {e}")
        return False

def test_google_sheets_connection():
    """Test Google Sheets API connection"""
    print("\n🔍 Testing Google Sheets connection...")
    
    try:
        from src.config import Config
        from src.google_api import GoogleAPIHandler
        
        if not Config.SPREADSHEET_ID or Config.SPREADSHEET_ID == 'your_spreadsheet_id_here':
            print("   ⚠️  SPREADSHEET_ID not configured - skipping test")
            return False
        
        handler = GoogleAPIHandler()
        
        # Try to read a small range
        rows = handler.read_sheet_rows("A1:A1")
        print(f"   ✅ Google Sheets connection successful!")
        print(f"   → Successfully accessed sheet: {Config.SHEET_NAME}")
        return True
        
    except Exception as e:
        print(f"   ❌ Google Sheets test failed: {e}")
        print(f"   → Make sure the sheet is shared with your service account")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🚀 GitHub Repository Evaluator - Setup Verification")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_service_account(),
        check_directories(),
    ]
    
    # API tests (optional)
    print("\n" + "=" * 60)
    print("🔌 Testing API Connections (optional)")
    print("=" * 60)
    
    api_checks = [
        test_gemini_connection(),
        test_google_sheets_connection(),
    ]
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    basic_checks_passed = all(checks)
    api_checks_passed = all(api_checks)
    
    if basic_checks_passed and api_checks_passed:
        print("✅ All checks passed! You're ready to run evaluations.")
        print("\n🚀 Next step:")
        print("   python scripts/evaluate_github_repos.py")
    elif basic_checks_passed:
        print("✅ Basic setup complete!")
        print("⚠️  Some API connections need configuration")
        print("\n📝 Check the errors above and update your .env file")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\n📖 Read QUICKSTART.md for detailed setup instructions")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
