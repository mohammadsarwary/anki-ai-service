# Anki AI Django Backend

Python/Django replacement backend for the Laravel + FastAPI split stack.

## What Is Included

- Django + Django REST Framework API compatible with the existing `/api/...` Laravel routes.
- Compatibility endpoints for the current AI service:
  - `GET /health`
  - `POST /api/v1/generate-flashcards`
  - `POST /api/v1/generate-from-topic`
  - `POST /api/v1/generate-practice-sentence`
- Unfold-powered Django admin, with a custom analytics dashboard at `/admin/analytics/`.
- DB-backed AI jobs for cPanel cron deployment.
- Laravel MySQL import command with UUID/timestamp preservation.
- Verify-only Laravel bcrypt login support. Successful legacy logins are upgraded to Django password hashes.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py collectstatic --dry-run --noinput
.\.venv\Scripts\python.exe -c "import passenger_wsgi; print(passenger_wsgi.application)"
```

## cPanel Deployment

1. Upload `django_backend/` to the Python app directory.
2. Create a Python app in cPanel and point it at `passenger_wsgi.py`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure `.env` with MySQL, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and AI provider keys.
5. Run:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
6. Add cPanel cron entries:
   ```bash
   * * * * * /path/to/python /path/to/django_backend/manage.py process_ai_jobs --max-seconds=50
   0 0 * * * /path/to/python /path/to/django_backend/manage.py generate_daily_challenges
   ```

## Import Laravel Data

Sanctum tokens are intentionally not imported. Users log in again with the same passwords.

```bash
python manage.py import_laravel_data \
  --host 127.0.0.1 \
  --port 3306 \
  --database anki_ai_laravel \
  --user root \
  --password secret
```
