@echo off
:: ==============================================================================
:: HMS Local Setup Script (Windows)
:: ==============================================================================
echo --- Starting HMS Local Setup ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: python is not installed.
    exit /b 1
)
echo Step 1: Creating virtual environment...
python -m venv venv
echo Step 2: Installing dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
    echo Step 3: Creating .env from template...
    copy .env.example .env
)
echo Step 4: Running migrations...
python manage.py migrate
echo --- Setup Finished! ---
echo Run 'python manage.py runserver' to start.
pause
