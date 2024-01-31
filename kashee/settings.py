from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = 'django-insecure-o!3kemb1c-ia##fg00ew@yy+&zs+!z)w@lh^22npx$r+&h-cw8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ["10.10.10.63","*"]
# ALLOWED_HOSTS = ["*","localhost"]

MEDIA_URL="/media/"
MEDIA_ROOT=os.path.join(BASE_DIR,"media")

STATIC_URL="/static/"
STATIC_ROOT="/static/"
STATICFILES_DIRS=[STATIC_DIR]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hrms',
    'channels',
    'crispy_forms',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'hrms.LoginCheckMiddleWare.LoginCheckMiddleWare'
]

ROOT_URLCONF = 'kashee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'kashee.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
}

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("127.0.0.1", 6379)],   # Change localhost to the ip in which you have redis server running on.
#         },
#     },
# }

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",  # Use InMemoryChannelLayer for development
        # "BACKEND": "channels_redis.core.RedisChannelLayer",  # Use this for production with Redis
        # "CONFIG": {
        #     "hosts": [("127.0.0.1", 6379)],
        # },
    },
}

ASGI_APPLICATION = 'kashee.routing.application'

# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DB_ENGINE = os.getenv('DB_ENGINE', None)
DB_USERNAME = os.getenv('DB_USER', None)
DB_PASS = os.getenv('DB_PASSWORD', None)
DB_HOST = os.getenv('DB_HOST', None)
DB_PORT = os.getenv('DB_PORT', None)
DB_NAME = os.getenv('DB_NAME', None)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kashee_hr',
        'USER': 'root',
        'PASSWORD': '@Kashee#12345',
        'HOST': 'localhost',
        'PORT': '3307',
    },
}


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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

AUTH_USER_MODEL="hrms.CustomUser"
AUTHENTICATION_BACKENDS=['hrms.EmailBackEnd.EmailBackEnd']


# EMAIL_HOST="smtp.gmail.com"
# EMAIl_PORT=587
# EMAIL_HOST_USER="GMAIL_EMAIL"
# EMAIL_HOST_PASSWORD="GMAIL PASSWORD"
# EMAIL_USE_TLS=True


# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# # EMAIL_BACKEND="django.core.mail.backends.filebased.EmailBackend"
# EMAIL_FILE_PATH=os.path.join(BASE_DIR,"sent_mails")
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True 
# EMAIL_HOST_USER = 'educard218@gmail.com'
# EMAIL_HOST_PASSWORD = 'uljoamupfgkdanxa'
# DEFAULT_FROM_EMAIL="Kashee HRMS educard218@gmail.com"

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.office365.com'  # Microsoft's SMTP server for Office 365
# EMAIL_PORT = 587  # Use port 587 for TLS
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'divyanshu.kumar@kasheemilk.com'  # Your Microsoft email address
# EMAIL_HOST_PASSWORD = 'Dok34845'  # Your email account password
# DEFAULT_FROM_EMAIL = 'divyanshu.kumar@kasheemilk.com'  # Your default sender email address
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'  # Microsoft's SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'divyanshu.kumar@kasheemilk.com'  # Your Microsoft 365 email
EMAIL_HOST_PASSWORD = 'Dok34845'  # Your Microsoft 365 email password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

#Enable Only Making Project Live on Heroku
# STATICFILES_STORAGE='whitenoise.storage.CompressedManifestStaticFilesStorage'
# import dj_database_url
# prod_db=dj_database_url.config(conn_max_age=500)
# DATABASES['default'].update(prod_db)

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
