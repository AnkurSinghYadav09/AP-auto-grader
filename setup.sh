#!/bin/bash

# Installation and Setup Script for GitHub Repository Evaluator
# This script automates the initial setup process

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         GitHub Repository Evaluator - Setup Script            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python version
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Python installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 3 found: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | awk '{print $2}')
    if [[ $PYTHON_VERSION == 3.* ]]; then
        print_success "Python 3 found: $PYTHON_VERSION"
        PYTHON_CMD="python"
    else
        print_error "Python 3.8+ required, found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.8 or higher"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    print_error "pip not found. Please install pip"
    exit 1
fi

print_success "pip found"
echo ""

# Create virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Setting up virtual environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        print_info "Removed existing virtual environment"
    else
        print_info "Keeping existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_success "Using existing virtual environment"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"
echo ""

# Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Installing dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_info "Installing Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

print_success "All dependencies installed"
echo ""

# Create necessary directories
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Creating directories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p credentials
mkdir -p logs
mkdir -p cloned_repos

print_success "credentials/ directory created"
print_success "logs/ directory created"
print_success "cloned_repos/ directory created"
echo ""

# Setup .env file
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Configuring environment variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Overwrite with template? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success ".env file created from template"
    else
        print_info "Keeping existing .env file"
    fi
else
    cp .env.example .env
    print_success ".env file created from template"
fi

print_warning "Please edit .env file and add your API keys:"
print_info "  - GEMINI_API_KEY (required)"
print_info "  - SPREADSHEET_ID (required)"
print_info "  - GITHUB_TOKEN (optional but recommended)"
echo ""

# Service account check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Checking Google Service Account"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "credentials/service_account.json" ]; then
    print_success "Service account file found"
    
    # Extract and display email
    if command -v jq &> /dev/null; then
        EMAIL=$(jq -r '.client_email' credentials/service_account.json)
        print_info "Service account email: $EMAIL"
        print_warning "Make sure to share your Google Sheet with this email!"
    fi
else
    print_warning "Service account file not found"
    print_info "Please download from Google Cloud Console"
    print_info "Save as: credentials/service_account.json"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Installation successful!"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   ${BLUE}nano .env${NC}"
echo ""
echo "2. Add your service account JSON:"
echo "   ${BLUE}credentials/service_account.json${NC}"
echo ""
echo "3. Verify setup:"
echo "   ${BLUE}python scripts/verify_setup.py${NC}"
echo ""
echo "4. Test with a single repository:"
echo "   ${BLUE}python scripts/evaluate_single_repo.py https://github.com/user/repo${NC}"
echo ""
echo "5. Run batch evaluation:"
echo "   ${BLUE}python scripts/evaluate_github_repos.py${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Documentation:"
print_info "  - README.md - Comprehensive guide"
print_info "  - QUICKSTART.md - 5-minute setup guide"
print_info "  - IMPLEMENTATION_SUMMARY.md - Technical details"
echo ""
print_success "Ready to evaluate GitHub repositories! 🚀"
echo ""
