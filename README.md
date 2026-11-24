# Somobay (CKBSSL)

A Django-based web application for **Chaka Khudra Byaboshayi Somobay Somiti Limited (CKBSSL)** to manage cooperative society clients, loans, repayments, savings deposits, withdrawals, and field employees.

## Tech Stack

- **Framework:** Django (`3.1.5` in `requirements.txt`)
- **Language:** Python (originally deployed on Python 3.7)
- **Database:** MySQL / PostgreSQL / SQLite (configurable via environment variables)
- **Frontend:** Django Templates, Bootstrap, jQuery, Owl Carousel, Font Awesome

## Project Apps

- **`account`** — Custom email-authenticated `User` model (`AUTH_USER_MODEL = 'account.User'`), `UserType` roles (`owner`, `employee`), role-based decorators (`owner_only`, `employee_only`), and login/logout views.
- **`owner`** — Owner dashboard and management routes: view all/running/date-over clients, add/edit/remove/search clients, add/edit/activate/remove employees, record loan returns, savings, withdrawals, and new loans, and review daily collections and recent entries.
- **`employee`** — Employee dashboard routes: view and search assigned clients, register new clients, view client details, and record loan returns, savings, withdrawals, and new loans.
- **`client`** — Core domain models (`Clients`, `LoanReturnDetails`, `SavingDetails`, `ProductDetails`) and client creation form (`ClientCreateForm`).

## Project Structure

```text
somobay/
├── account/          # Custom user model, auth forms, role decorators, login/logout views
├── client/           # Client, loan return, saving, and product models + migrations
├── employee/         # Employee models, forms, and dashboard views
├── owner/            # Owner views, forms, and URL routing
├── somobay/          # Django project settings, root URLs, WSGI/ASGI entrypoints
├── static/           # Source CSS, JS, images, and vendor assets
├── staticfiles/      # Collected static assets (STATIC_ROOT)
├── media/            # Media directory (MEDIA_ROOT)
├── templates/        # HTML templates (base, account, employee, owner)
├── manage.py         # Django management CLI
├── requirements.txt  # Python package dependencies
├── .env.example      # Example environment configuration template
└── .gitignore        # Git ignore rules
```

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/tariqulneightn/somobay.git
cd somobay
```

### 2. Create and activate a virtual environment

> **Note:** `requirements.txt` pins `Django==3.1.5` (and `somobay/urls.py` uses `django.conf.urls.url`, which was removed in Django 4.0). Using Python 3.7–3.9 is recommended for compatibility with Django 3.1.5.

```bash
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Database driver note:** `requirements.txt` includes `psycopg2==2.8.6` (PostgreSQL). If you use MySQL (`DB_ENGINE=django.db.backends.mysql`), install a compatible MySQL driver such as `mysqlclient` in your environment.

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Environment variables supported by `somobay/settings.py` and `account/views.py`:

| Variable | Description | Example |
| --- | --- | --- |
| `SECRET_KEY` | Django cryptographic secret key (**required**) | `replace-with-random-secret` |
| `DEBUG` | Enable debug mode (`True` or `False`) | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `127.0.0.1,localhost` |
| `DB_ENGINE` | Django database backend | `django.db.backends.sqlite3` or `django.db.backends.mysql` |
| `DB_NAME` | Database name (or SQLite filename) | `db.sqlite3` |
| `DB_USER` | Database username (non-SQLite) | `somobay_user` |
| `DB_PASSWORD` | Database password (non-SQLite) | `strong-password` |
| `DB_HOST` | Database host (non-SQLite) | `127.0.0.1` |
| `DB_PORT` | Database port (non-SQLite) | `3306` |
| `DEFAULT_OWNER_NAME` | Optional initial owner name when `User` table is empty | `Owner Name` |
| `DEFAULT_OWNER_EMAIL` | Optional initial owner login email | `owner@example.com` |
| `DEFAULT_OWNER_PASSWORD` | Optional initial owner password | `change-me` |
| `DEFAULT_OWNER_PHONE` | Optional initial owner phone | `+8801XXXXXXXXX` |

### 5. Run database migrations & start the server

```bash
python manage.py migrate
python manage.py runserver
```

If you leave `DEFAULT_OWNER_EMAIL` / `DEFAULT_OWNER_PASSWORD` blank, create an admin user manually after migrating (ensure `UserType` records `owner` and `employee` exist by visiting `/` or adding them in Django admin).

## Static Files & Deployment Notes

- `staticfiles/` and `media/` are tracked in this repository. When source assets in `static/` change, update collected files with:
  ```bash
  python manage.py collectstatic
  ```
- Local environment files (`.env`), log files (`*.log`), SQLite databases (`*.sqlite3`), Python caches (`__pycache__/`, `*.pyc`), and cPanel/Passenger hosting files (`.htaccess`, `passenger_wsgi.py`, `backup/`, `tmp/`, `public/`) are excluded in `.gitignore`.
- Before deploying to production, ensure `DEBUG=False`, set a strong unique `SECRET_KEY`, and configure `ALLOWED_HOSTS` and database credentials securely on the server.
