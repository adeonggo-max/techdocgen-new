#!/bin/bash
# Script to run the Streamlit UI

echo "🚀 Starting TechDocGen Web UI..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Run Streamlit
echo "🌐 Launching web interface..."
echo ""
streamlit run app.py







