#!/bin/bash

# Project Chimera Setup Script
# This script helps new users set up the development environment quickly

echo "🧪 Setting up Project Chimera..."

# Check if Python 3.9+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.9 or later."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Found Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your configuration before running simulations"
else
    echo "✅ Environment configuration already exists"
fi

# Check if Docker is available (optional)
if command -v docker &> /dev/null; then
    echo "🐳 Docker found - you can use containerized models"
else
    echo "ℹ️  Docker not found - you'll need to use local or API-based models"
fi

echo ""
echo "🎉 Setup complete! To get started:"
echo "   1. Edit .env file with your API keys or model configurations"
echo "   2. Activate the virtual environment: source venv/bin/activate"
echo "   3. Run a test simulation: python3 run_hierarchical_simulation.py --steps 5 --scenario 'Test'"
echo ""
echo "📚 Check the README.md for more detailed instructions"
echo "🔬 Happy researching!"
