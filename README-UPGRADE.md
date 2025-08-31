# AIF Compliance — Upgrade Bundle

This bundle includes fixes and production-ready enhancements:
- Added `docgen` app config (`docgen/apps.py`) and `__init__.py`, plus admin registrations.
- Added safe defaults to `aif_compliance/settings.py`:
  - DRF defaults (auth, pagination, filters, throttling)
  - Optional Redis cache (`USE_REDIS=1` + `REDIS_URL`)
  - Security toggles via env: SSL redirect, secure cookies, HSTS
  - WhiteNoise static files
- Wired `docgen` API route into `aif_compliance/urls.py`.
- Created `requirements.txt` with core packages.
- Normalized packages by creating missing `__init__.py` files in Python subpackages.
- Updated `.env.example` with production-ready variables.

## How to run (dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# (optional) export USE_REDIS=0
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=dev-key
python manage.py migrate
python manage.py runserver
```

## How to run (prod-like)

- Use **PostgreSQL** and set `DATABASE_URL`.
- Use **Redis** (`USE_REDIS=1` and `REDIS_URL`).
- Set:
  ```bash
  export DJANGO_DEBUG=False
  export DJANGO_ALLOWED_HOSTS=your.domain,www.your.domain
  export DJANGO_SECURE_SSL_REDIRECT=1
  export DJANGO_SESSION_COOKIE_SECURE=1
  export DJANGO_CSRF_COOKIE_SECURE=1
  export DJANGO_HSTS_SECONDS=31536000
  export DJANGO_HSTS_INCLUDE_SUBDOMAINS=1
  export DJANGO_HSTS_PRELOAD=1
  ```
- Collect static:
  ```bash
  python manage.py collectstatic --noinput
  ```

## Notes

- If you use S3 for media, set `DEFAULT_FILE_STORAGE` and `MEDIA_URL` accordingly.
- Consider adding Sentry (`sentry-sdk`) and JWT auth if you expose APIs publicly.
- For large imports/generation tasks, add Celery + Beat to offload to background workers.

