# aif_compliance/settings_production.py
from .settings import *  # noqa
import os

DEBUG = False

# Fail fast if secrets are missing
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('DJANGO_CSRF_TRUSTED', '').split(',')

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# DB persistent connections (no schema change)
CONN_MAX_AGE = 60

# Static files caching with WhiteNoise (safe)
INSTALLED_APPS = list(INSTALLED_APPS)
if 'whitenoise' not in ''.join(MIDDLEWARE):
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        *[m for m in MIDDLEWARE if m not in ['whitenoise.middleware.WhiteNoiseMiddleware','django.middleware.security.SecurityMiddleware']]
    ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging to stdout in JSON
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s","module":"%(module)s","line":%(lineno)d}'
        }
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'json'}
    },
    'root': {'handlers': ['console'], 'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.security': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
