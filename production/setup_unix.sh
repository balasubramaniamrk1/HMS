#!/bin/bash
# ==============================================================================
# HMS Local Setup Script (Unix/Mac)
# ==============================================================================
echo "--- Starting HMS Local Setup ---"
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi
echo "Step 1: Creating virtual environment..."
python3 -m venv venv
echo "Step 2: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
if [ ! -f .env ]; then
    echo "Step 3: Creating .env from template..."
    cp .env.example .env
fi
echo "Step 4: Running migrations..."
python manage.py migrate
echo "--- Setup Finished! ---"
echo "Run 'python manage.py runserver' to start."
