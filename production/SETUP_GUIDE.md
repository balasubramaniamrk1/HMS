# HMS Local Installation Guide (Non-Docker)

This guide provides step-by-step instructions for setting up the Hospital Management System (HMS) on your local machine using Python, Django, and PostgreSQL.

## 1. Prerequisites

Ensure you have the following installed on your system:
- **Python 3.10+**: [Download here](https://www.python.org/downloads/)
- **PostgreSQL**: [Download here](https://www.postgresql.org/download/)
- **Nginx**: 
    - Windows: [Download here](https://nginx.org/en/download.html)
    - Linux: `sudo apt install nginx`
- **Git**: [Download here](https://git-scm.com/downloads)

---

## 2. Database Setup

You must create a PostgreSQL database and user before running the application.

1. Open your PostgreSQL terminal (`psql`) or a tool like pgAdmin.
2. Run the following commands:
   ```sql
   CREATE DATABASE hms_db;
   CREATE USER hms_user WITH PASSWORD 'your_secure_password_here';
   GRANT ALL PRIVILEGES ON DATABASE hms_db TO hms_user;
   ```

---

## 3. Automated Setup

We have provided scripts to automate the Python environment and dependency installation.

### For Mac/Linux:
1. Open terminal in the project root.
2. Run: `bash production/setup_unix.sh`

### For Windows:
1. Open Command Prompt in the project root.
2. Run: `production\setup_windows.bat`

---

## 4. Manual Installation Steps

### Step 1: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # (Linux/Mac only)
```

### Step 3: Configure Environment Variables
1. Copy the example file: `cp .env.example .env`
2. Update `.env` with your local PostgreSQL credentials.

### Step 4: Run Migrations & Collect Static
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 5. Web Server Setup (Nginx)

To run in "Production Mode" locally, use Nginx as a reverse proxy.

### On Linux (Ubuntu/Debian):
1. Copy the config: `sudo cp production/hms_nginx_linux.conf /etc/nginx/sites-available/hms`
2. Link it: `sudo ln -s /etc/nginx/sites-available/hms /etc/nginx/sites-enabled`
3. Start Gunicorn:
   ```bash
   gunicorn --workers 3 --bind unix:/run/hms.sock hms_project.wsgi:application
   ```
4. Restart Nginx: `sudo systemctl restart nginx`

### On Windows:
1. Copy `production/hms_nginx_windows.conf` to your Nginx `conf/` folder.
2. Update the `alias` paths in the config to point to your local project directory.
3. Start the Django server: `python manage.py runserver` (or use a production server like Waitress).
4. Start Nginx.

---

## 6. Accessing the App
The application will be available at `http://localhost` (via Nginx) or `http://127.0.0.1:8000` (Directly).
