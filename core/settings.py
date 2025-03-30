"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path

from environs import Env

# Read environment variables
env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Installed apps
    "django_celery_beat",
    "tinymce",
    "django_cleanup",
    # Local apps
    "bank",
    "common",
    "chronopost",
    "profiles",
    "robot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("POSTGRES_USER", "user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = [
    "profiles.auth_backends.TelegramOrUsernameAuthBackend",
    "django.contrib.auth.backends.ModelBackend",  # Стандартний бекенд
]

AUTH_USER_MODEL = "profiles.ClubUser"  # User model

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "uk"

TIME_ZONE = "Europe/Kyiv"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_DIR = os.path.join(BASE_DIR, "static").replace("\\", "/")

# Use STATICFILES_DIRS in debug mode and STATIC_ROOT in production
STATICFILES_DIRS = [STATIC_DIR] if DEBUG else []
STATIC_ROOT = None if DEBUG else STATIC_DIR

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media").replace("\\", "/")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Telegram bot settings
TELEGRAM_BOT_TOKEN = env.str("TELEGRAM_BOT_TOKEN")  # Bot token
DEFAULT_CHAT_ID = env.int("DEFAULT_CHAT_ID")  # Default chat ID
ADMINS_BOT = env.list("ADMINS_BOT", subcast=int)
TELEGRAM_WEBHOOK_URL = env.str("BASE_URL") + env.str("TELEGRAM_WEBHOOK_PATH")

# Bank settings
BASE_URL = env.str("BASE_URL")
MONOBANK_WEBHOOK_PATH = env.str("MONOBANK_WEBHOOK_PATH")

# REDIS connection
REDIS_HOST = "0.0.0.0"
REDIS_PORT = "6379"

# Redis connection
REDIS_URL_TEMPLATE = "redis://{host}:{port}/{db}"
REDIS_HOST = REDIS_HOST if DEBUG else "django_redis"
REDIS_PORT = REDIS_PORT if DEBUG else "6379"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL_TEMPLATE.format(
            host=REDIS_HOST, port=REDIS_PORT, db=3
        ),  # Redis URL
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


CELERY_BROKER_URL = REDIS_URL_TEMPLATE.format(
    host=REDIS_HOST, port=REDIS_PORT, db=0
)
CELERY_RESULT_BACKEND = REDIS_URL_TEMPLATE.format(
    host=REDIS_HOST, port=REDIS_PORT, db=1
)

# Robot redis settings
BOT_STORAGE_URL = REDIS_URL_TEMPLATE.format(
    host=REDIS_HOST, port=REDIS_PORT, db=4
) if os.environ.get("USE_REDIS_WITH_BOT") else None

# Celery settings
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 3600}
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Kyiv"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# OpenWeatherMap settings
WEATHER_API_KEY = env.str("WEATHER_API_KEY")
CITY_COORDINATES = env.list("CITY_COORDINATES", subcast=float)

# TinyMCE settings
TINYMCE_DEFAULT_CONFIG = {
    "height": 300,
    "width": 800,
    "forced_root_block": "",
    "force_br_newlines": True,
    "force_p_newlines": False,
    "menubar": False,
    "plugins": "advlist autolink lists link code codesample preview emoticons",
    "toolbar": "undo redo | bold italic underline strikethrough | emoticons | link codesample code | "
    "preview",
    "valid_elements": "p,br,b,strong,i,em,u,ins,s,strike,a[href|target],code,pre",
    "emoticons_database": "emojis",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",  # Рівень логування
            "class": "logging.StreamHandler",  # Вивід у консоль
            "formatter": "console",
        },
    },
    "loggers": {
        "": {  # Кореневий логер (для всіх логерів)
            "handlers": ["console"],
            "level": "INFO",  # Рівень логування для кореневого логера
            "propagate": True,
        },
        "django": {  # Логер для Django
            "handlers": ["console"],
            "level": "INFO",  # Рівень логування для Django
            "propagate": False,
        },
        "chronopost": {  # Логер для вашого додатку
            "handlers": ["console"],
            "level": "INFO",  # Рівень логування для вашого додатку
            "propagate": False,
        },
    },
}
