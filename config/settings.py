# config/settings.py
from pathlib import Path
import os
from celery.schedules import schedule
from celery.schedules import crontab 
#  &larr; для CELERY_BEAT_SCHEDULE

# ----------------------------------------------------------------------------------
# ОСНОВНОЕ
# ----------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-2@p0*5mhpo(2!r@ox=%7ozr@yy!oc1-eazkrfcpw8g+fr*3q%f"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

# ----------------------------------------------------------------------------------
# ПРИЛОЖЕНИЯ
# ----------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project
    "monitoring",
    # 3‑rd party
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    # Celery мониторинг
    "django_celery_results",
    "django_celery_beat",
    "dashboard"
]

# ----------------------------------------------------------------------------------
# СРЕДНИЙ СЛОЙ
# ----------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
TEMPLATES[0]["DIRS"].append(BASE_DIR / "templates")

WSGI_APPLICATION = "config.wsgi.application"

STATICFILES_DIRS = [
    BASE_DIR / "static",      # <— новый каталог
]

# ----------------------------------------------------------------------------------
# БАЗА ДАННЫХ (PostgreSQL)
# ----------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "FireDetection",
        "USER": "postgres",
        "PASSWORD": "12345678",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# ----------------------------------------------------------------------------------
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ----------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------------------
# DRF
# ----------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ----------------------------------------------------------------------------------
# I18N
# ----------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
CELERY_TIMEZONE = TIME_ZONE 

# ----------------------------------------------------------------------------------
# СТАТИКА
# ----------------------------------------------------------------------------------
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------------------------------------
# CELERY / REDIS
# ----------------------------------------------------------------------------------
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
CELERY_TIMEZONE = TIME_ZONE            # 'UTC'
CELERY_IMPORTS = ("monitoring.tasks",)

CELERY_BEAT_SCHEDULE = {
    # 1) генерация телеметрии
    "generate_env_every_5s": {
        "task": "monitoring.tasks.generate_random_data",
        "schedule": crontab(minute="*/10"),                # каждые 5 с
    },
    # 2) пакетный расчёт пожарной опасности
    "calc_hazard_every_5s": {
        "task": "monitoring.tasks.calculate_hazard_batch",
        "schedule": crontab(minute="*/10"),
    },
    # 3) ночная чистка сырых данных старше 30 дней
    "purge_old_env_daily": {
        "task": "monitoring.tasks.purge_old_env",
        "schedule": crontab(hour=3, minute=0),
    },
}