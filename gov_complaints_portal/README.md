# Government Online Complaint Portal

A full Django template-based web application for filing, tracking, and managing government complaints with PostgreSQL.

## Features
- User signup, login/logout, password reset, and profile page.
- Complaint submission with reference IDs (`GOV-CMP-YYYY-000001` style).
- Multiple attachments (images/PDF), secure download/view endpoint, and validation.
- Role-based permissions:
  - Users can view only their own complaints.
  - Users can edit/delete only when status is `received`.
  - Staff can view all complaints and update status/assignment/remarks.
- Staff internal comment timeline.
- Search, filter, date range filtering, and pagination (10 per page).
- Email notifications:
  - On complaint submission.
  - On status change.
- Bootstrap 5 UI with Django messages.
- Single-click copy buttons on complaint detail page:
  - Copy complaint reference ID.
  - Copy page URL.

## Project Structure
```text
gov_complaints_portal/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── gov_portal/
├── complaints/
├── templates/
├── static/
└── media/
```

## PostgreSQL Setup
1. Install PostgreSQL and ensure the server is running.
2. Create a database and user:
   - Database: `gov_complaints` (or your preferred name)
   - User/password: as configured in `.env`
3. Grant required privileges to the user.

Example SQL:
```sql
CREATE DATABASE gov_complaints;
CREATE USER gov_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE gov_complaints TO gov_user;
```

## Environment Variables
1. Copy `.env.example` to `.env`.
2. Set at minimum:
   - `SECRET_KEY`
   - `DEBUG`
   - `ALLOWED_HOSTS`
   - Either `DATABASE_URL` or `DB_*` PostgreSQL settings
3. Configure SMTP values if needed; default is console email backend.

## Setup and Run
Run these commands from `gov_complaints_portal/`:

```bash
python -m venv venv
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Manage.py Command Guide
- Run server:
```bash
python manage.py runserver
```
- Create migrations:
```bash
python manage.py makemigrations
```
- Apply migrations:
```bash
python manage.py migrate
```
- Create superuser:
```bash
python manage.py createsuperuser
```
- Seed sample data:
```bash
python manage.py seed_data
```
- Run tests:
```bash
python manage.py test
```

## Development Notes
- Attachments are stored in `media/`.
- Files are served securely through app views with permission checks.
- Avoid exposing `MEDIA_URL` directly in production without authorization controls.

## Production Notes
- Set `DEBUG=False`.
- Use a production-grade server (`gunicorn`/`uvicorn` + reverse proxy).
- Configure static/media hosting and secured file serving strategy.
- Use a strong `SECRET_KEY` and secure cookie settings.

## Screenshot Placeholders
- [Screenshot Placeholder: Home]
- [Screenshot Placeholder: Complaint List]
- [Screenshot Placeholder: Complaint Detail - Copy Buttons]
- [Screenshot Placeholder: Staff Dashboard]
