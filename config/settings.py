# Copyright (c) 2026 Dafa Al Hafiz. All rights reserved.
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

# Domain produksi diisi lewat env (pisahkan dengan koma), mis:
# CSRF_TRUSTED_ORIGINS=https://namadomain.my.id
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.ngrok-free.dev').split(',') if o.strip()
]

# CORS — hanya dibutuhkan REST API (app Flutter). Nonaktif karena fokus web.
# CORS_ALLOWED_ORIGINS = [
#     'http://127.0.0.1:8080',
#     'http://localhost:8080',
#     'http://192.168.100.9:8080',
# ]
# CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST API (app Flutter) — nonaktif, fokus web. Aktifkan bila mobile dilanjut:
    # 'corsheaders',
    # 'rest_framework',

    'apps.master',
    'apps.operasional',
    'apps.tangkap',
    'apps.penjualan',
    'apps.laporan',
    'apps.core',
    'apps.api',
]

MIDDLEWARE = [
    # 'corsheaders.middleware.CorsMiddleware',  # REST API (Flutter) — nonaktif
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve static di production/gunicorn
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.core.middleware.DemoWindowMiddleware',  # tutup akses demo setelah DEMO_OPEN_UNTIL
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Jendela demo: tutup akses publik setelah waktu ini (kosong = selalu buka).
# Format waktu lokal Asia/Jakarta, mis. "2026-06-24 12:30".
DEMO_OPEN_UNTIL = os.environ.get('DEMO_OPEN_UNTIL', '').strip()
# Kunci opsional untuk melewati penutupan: buka https://domain/?buka=KUNCI
DEMO_BYPASS_KEY = os.environ.get('DEMO_BYPASS_KEY', '').strip()

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.user_role',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Postgres bila env DB tersedia (Docker), selain itu SQLite (dev lokal).
if os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: compress + hash (cache-busting) untuk static di gunicorn
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Media: foto bukti penjualan & tangkap
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session berakhir saat browser ditutup (bukan persistent cookie)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600

# ── Pengamanan produksi (aktif saat DEBUG=False, mis. di belakang Caddy/HTTPS) ──
if not DEBUG:
    # Caddy/Nginx meneruskan header proto; percayai agar Django tahu request HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
    SECURE_HSTS_SECONDS = 2592000          # 30 hari
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Konfigurasi REST API (app Flutter) — nonaktif, fokus web.
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ),
#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 50,
# }
#
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
# }

# Firebase Cloud Messaging — isi path ke service account JSON dari Firebase Console.
# Kosongkan jika belum setup; FCM dilewati, Notification DB tetap jalan.
FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
