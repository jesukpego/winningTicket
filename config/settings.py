from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _
import dj_database_url

# ==================== BASE ====================
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"

# ==================== HOSTS ====================
ALLOWED_HOSTS = ["*", "127.0.0.1", "localhost", "abcd-8000.use.devtunnels.ms", ".use.devtunnels.ms","merle-pruriginous-positively.ngrok-free.dev","3mvm0nfm-8000.use.devtunnels.ms"]
CSRF_TRUSTED_ORIGINS = [
    "https://*.use.devtunnels.ms",
    "https://3mvm0nfm-8000.use.devtunnels.ms",
    "https://abcd-8000.use.devtunnels.ms",
    "https://*.railway.app",
    "https://merle-pruriginous-positively.ngrok-free.dev",  # ton lien ngrok
    "https://*.ngrok-free.dev"  # optionnel pour tous les sous-domaines ngrok
]




# ==================== DATABASE ====================
# Detect Railway environment safely
RAILWAY_ENVIRONMENT = os.environ.get("RAILWAY_ENVIRONMENT")
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'pcznpmUWZTZxvfsBTdrPGXxZYoeSSGpW',
        'HOST': 'gondola.proxy.rlwy.net',
        'PORT': '46452',
        'OPTIONS': {
            'sslmode': 'require',
        }
    }
}
# Only use Railway config if we are in Railway AND have a database URL
""" if RAILWAY_ENVIRONMENT and DATABASE_URL:
    # ===== PRODUCTION (Railway - PostgreSQL) =====
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # ===== LOCAL DEVELOPMENT (SQLite) =====
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    } """

   

# ==================== APPLICATION ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'principal',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # i18n support
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'config.urls'

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
                'django.template.context_processors.i18n',
                'principal.context_processors.navigation_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==================== STATIC FILES ====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==================== MEDIA ====================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==================== I18N ====================
LANGUAGE_CODE = 'fr'  # Default language: French
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True
# Ajoute ceci pour stabiliser le choix de la langue
LANGUAGE_COOKIE_NAME = 'django_language'

# Supported languages
LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
]
# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'config' / 'locale',
]

# ==================== SECURITY (PROD ONLY) ====================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==================== AUTH ====================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
