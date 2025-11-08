# 🎓 College Management System (Backend) — Django + DRF

A robust backend system for managing college events, users, roles, certificates, attendance, and notifications.  
Built using Django & Django REST Framework with a clear workflow for event lifecycle: **Create → Request Approval → Approve/Reject → Publish → Register → Feedback → Certificate.**

This repository contains **backend-only implementation**. The system can be easily connected to any frontend (React recommended).

> **Note:** Payment Gateway Integration (Khalti/eSewa) is not included in this version.

---

## ✨ Features

### 👥 Role-Based Access
- **Admin**
- **Campus-Chief / Faculty / Department**
- **Organization / Clubs**
- **Students**

### 👤 User & Profile Management
- Department & batch/semester mapping
- Profile and basic user info fields
- Auth using **Django Authentication + Token / Session**

### 🎉 Event Management Workflow
| Stage | Description |
|------|-------------|
| Create | Organizer submits event details |
| Approval | Faculty/Campus-Chief/Administrator reviews |
| Publish | Approved events become visible to students |
| Participation | Students register or cancel registration |
| Feedback | Students submit feedback after completion |

### ✅ Additional Features
- **QR-based Attendance**
- **In-App + Email Notifications**
- **Auto Certificate Generation (PDF)**
- **Dashboard Statistics for Each Role**
- **Pluggable Celery Tasks for periodic jobs**

---

## 🛠 Tech Stack

| Layer | Technology |
|------|------------|
| Backend | Django 4.x, Django REST Framework |
| Auth | Session + Token Based Auth |
| Database | SQLite (Dev) → PostgreSQL (Recommended for Deployment) |
| Tasks (Optional) | Celery + Redis |
| Email | Django Email Backend (Console for Dev) |
| CORS | django-cors-headers |

---

🗂 #Project Structure
```
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
```

🚀 Getting Started
```
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
