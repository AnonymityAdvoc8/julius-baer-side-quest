#!/bin/bash
# Setup script for Banking Client
# Automatically creates Python 3.12 virtual environment and installs dependencies

set -e  # Exit on error

echo "🏦 Banking Client - Setup Script"
echo "=================================="
echo ""

# Check if python3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Error: python3.12 not found!"
    echo ""
    echo "Please install Python 3.12 first:"
    echo "  - macOS: brew install python@3.12"
    echo "  - Ubuntu/Debian: sudo apt install python3.12 python3.12-venv"
    echo "  - Download: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3.12 found: $(python3.12 --version)"
echo ""

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Removing old virtual environment..."
        rm -rf venv
    else
        echo "📦 Using existing virtual environment"
        SKIP_VENV=true
    fi
fi

if [ "$SKIP_VENV" != "true" ]; then
    echo "🔧 Creating Python 3.12 virtual environment..."
    python3.12 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "📦 Installing dependencies..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the banking server (in another terminal):"
echo "   docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest"
echo ""
echo "3. Run the client:"
echo "   python main.py transfer --from ACC1000 --to ACC1001 --amount 100"
echo ""
echo "Or use make commands:"
echo "   make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'"
echo "   make demo"
echo "   make test"
echo ""
echo "For more commands, run: make help"
echo ""

