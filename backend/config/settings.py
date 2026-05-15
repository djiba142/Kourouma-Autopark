"""
BSG Web — settings.py
SQLite en développement, PostgreSQL en production (Render.com).
JWT supprimé — auth par sessions Django (plus simple pour le web).
"""
import os, sys
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'bsg-web-dev-secret-change-in-prod-xyz987')
DEBUG      = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # Bibliothèques tierces
    'rest_framework',
    'corsheaders',
    'django_filters',
    'django_rest_passwordreset',
    # Apps métier (réutilisées du backend mobile)
    'auth_users',
    'produits',
    'stock',
    'commandes',
    'clients',
    'achats',
    'finances',
    'audit',
    'dashboard',
    'factures',
    'notifications',
    # App web (nouvelles vues HTML)
    'web',
    'ia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Audit automatique de toutes les requêtes
    'web.middleware.AuditMiddleware',
]

ROOT_URLCONF  = 'config.urls'
AUTH_USER_MODEL = 'auth_users.Utilisateur'
LOGIN_URL       = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

AUTHENTICATION_BACKENDS = [
    'auth_users.backends.EmailOrPhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # dossier templates global
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Contexte global : rôle, alertes stock, etc.
                'web.context_processors.bsg_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Base de données ────────────────────────────────────────────────────────────
# ── Base de données (MySQL par défaut) ────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'mysql://root:@127.0.0.1:3306/db_bsg'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
# Si MySQL, on ajoute les options spécifiques (pour compatibilité Render Postgres/Local MySQL)
if 'mysql' in DATABASES['default']['ENGINE']:
    DATABASES['default']['OPTIONS'] = {
        'charset': 'utf8',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=OFF",
    }

# ── Sessions ───────────────────────────────────────────────────────────────────
SESSION_ENGINE          = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE      = 60 * 60 * 10   # 10 heures
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE   = not DEBUG       # True en prod (HTTPS)

# ── Fichiers statiques et médias ───────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr'
TIME_ZONE     = 'Africa/Conakry'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Messages (alertes Bootstrap) ──────────────────────────────────────────────
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}

# ── Rest Framework ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# ── Sécurité production ────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS        = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT        = True
    CSRF_COOKIE_SECURE         = True
    SESSION_COOKIE_SECURE      = True
