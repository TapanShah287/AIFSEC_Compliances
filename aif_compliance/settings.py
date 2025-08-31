# aif_compliance/settings.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'insecure-dev-key')

# SECURITY WARNING: don't run with debug with true in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('1','true','yes')

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if not DEBUG else []

# Application definition
INSTALLED_APPS = [
    'taggit',
    'rest_framework',
    'transactions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'investors', 
    'manager_entities',
    'investee_companies',
    'funds',
    'compliances',
    'docgen',
    'dashboard',
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/portal/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aif_compliance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'aif_compliance.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


DEFAULT_ROUTER_TRAILING_SLASH = r'/?'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media Files - To handle uploaded documents
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Simple in-memory cache (safe default). Override via env for prod.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-app-cache'
    }
}


# --- Security hardening (only effective when DEBUG is False) ---
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', 'True').lower() in ('1','true','yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    CSRF_TRUSTED_ORIGINS = [u for u in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if u]



# --- Logging: surface slow queries and errors ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_DB_LOG_LEVEL', 'WARNING'),  # set to DEBUG in dev to see queries
        },
    },
}



# --- Template loader caching in production ---
if not DEBUG:
    for tpl in TEMPLATES:
        if 'OPTIONS' in tpl and 'loaders' not in tpl.get('OPTIONS', {}):
            tpl['OPTIONS']['loaders'] = [
                ('django.template.loaders.cached.Loader', tpl.get('OPTIONS', {}).get('loaders', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]))
            ]



# === Added by audit (safe defaults & prod-ready toggles) ===
# Security & hosts
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SECURE_SSL_REDIRECT = bool(int(os.getenv('DJANGO_SECURE_SSL_REDIRECT', '0')))
SESSION_COOKIE_SECURE = bool(int(os.getenv('DJANGO_SESSION_COOKIE_SECURE', '0')))
CSRF_COOKIE_SECURE = bool(int(os.getenv('DJANGO_CSRF_COOKIE_SECURE', '0')))
SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(int(os.getenv('DJANGO_HSTS_INCLUDE_SUBDOMAINS','0')))
SECURE_HSTS_PRELOAD = bool(int(os.getenv('DJANGO_HSTS_PRELOAD','0')))

# DRF defaults
if 'rest_framework' in INSTALLED_APPS and 'REST_FRAMEWORK' not in globals():
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
        "PAGE_SIZE": 50,
        "DEFAULT_FILTER_BACKENDS": [
            "django_filters.rest_framework.DjangoFilterBackend",
            "rest_framework.filters.SearchFilter",
            "rest_framework.filters.OrderingFilter",
        ],
        "DEFAULT_THROTTLE_RATES": {"user": "600/min", "anon": "60/min"},
    }

# Caches (Redis if enabled)
if os.getenv("USE_REDIS", "0") in ("1","true","True"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
else:
    CACHES = globals().get("CACHES", {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})

# Static files: enable WhiteNoise if present
MIDDLEWARE = list(MIDDLEWARE)
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    # Insert after SecurityMiddleware if present
    try:
        idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1
    except ValueError:
        idx = 0
    MIDDLEWARE.insert(idx, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Ensure required apps are present
try:
    INSTALLED_APPS = list(INSTALLED_APPS)
except NameError:
    INSTALLED_APPS = []
for app_name in ["django_filters", "docgen"]:
    if app_name not in INSTALLED_APPS:
        INSTALLED_APPS.append(app_name)
