#!/bin/bash
# Analytics Dashboard Startup Script

echo "🚀 Starting CollegeAdvisor Analytics Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start the dashboard
echo "Starting dashboard on http://localhost:5000"
python app.py