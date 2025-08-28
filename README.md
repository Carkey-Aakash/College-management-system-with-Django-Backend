# College-management-system-with-Django-Backend
College Management System — Django Backend

A Django + DRF backend for managing a college: users & roles, events (request → approval → publish), registrations, feedback, certificates, and notifications.

Scope note: This project does not include any payment gateway integration.

✨ Features

Role-based auth: Students, Faculty/Department, Organization, Admin,Campus-Chief

User & Profile: Departments, batches(semesters/years) , basic profile fields

Events module: Create → submit for approval → approve/reject → publish

Student actions: view approved events , Register / cancel registration, give feedback, view certificates

Approvals & workflow: Status tracking (pending/approved/cancelled/completed)

Notifications: In-app + email Notifications 

Dashboards/Stats: Aggregate counts per role(Department,Admin,Student,campus-chief,organization)

Clean DRF setup: Serializers, permissions, filters,.......

Tasks ready: Celery beat artifacts present for periodic jobs (if you enable Celery)

🗂 #Project Structure
College-management-system-with-Django-Backend/
├─ manage.py
├─ eventify/                # Project config (settings, urls, asgi/wsgi)
├─ users/                   # User model, roles, auth endpoints
├─ events/                  # Events, approvals, registrations, feedback,attendance
├─ notifications/           # Notification utilities (email/in-app)
├─ certificate/             # Certificate generation/related endpoints
├─ media/                   # Uploaded media (dev)
├─ celerybeat-schedule.*    # Celery beat state files (optional tasks)
└─ README.md


🛠 Tech Stack

Frameworks: Django 4.x, Django REST Framework

Auth: Token based and Session based

DB: PostgreSQL (recommended) but currently SQLite (dev)

CORS: django-cors-headers

Optional: Celery + Redis for async/periodic tasks; email backend for outbound mail

🚀 Getting Started

1) Clone & Create venv
git clone https://github.com/Carkey-Aakash/College-management-system-with-Django-Backend.git
cd College-management-system-with-Django-Backend

python -m venv .env

# Windows:
.\env\Scripts\activate

# macOS/Linux:
source .\env/bin/activate

2) Install requirements
pip install -r requirements.txt

3) Configure environment
Create a .env (or use your settings module directly). Example:

# Django
DEBUG=True
SECRET_KEY=change-this-in-production
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (Postgres recommended)
DB_NAME=college_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000


# Email (optional; console backend for dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@example.com

If your settings use a different config method, adapt accordingly.

4) Database setup

python manage.py migrate
python manage.py createsuperuser

5) Run dev server
python manage.py runserver


API root: http://127.0.0.1:8000/