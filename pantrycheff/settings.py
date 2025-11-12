from decouple import config
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!r1txr5^6d_a$i7g3*3-40-m*^vp%9+b#$-j#2ls15ss@$bjgb'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 'storages',
    'tailwind',
    'pantrycheff_tailwind',
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',

    # All_auth for user authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Tailwind CSS configuration
TAILWIND_APP_NAME = 'pantrycheff_tailwind'
NPM_BIN_PATH = 'npm.cmd'
INTERNAL_IPS = ['127.0.0.1',]

ROOT_URLCONF = 'pantrycheff.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'pantrycheff.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Postgresql database for production
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASS'),
#         'HOST': config('DB_HOST'),
#         'PORT': config('DB_PORT'),
#     }
# }

# # Redis cache configuration for production deployment
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": config("REDIS_URL"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }

# AWS credentials and configuration for the application
# AWS_ACCESS_KEY_ID= config('AWS_ACCESS_KEY_ID')
# AWS_REGION_ENDPOINT= config('AWS_REGION_ENDPOINT')
# AWS_REGION_NAME= config('AWS_REGION_NAME')
# AWS_S3_SIGNATURE_NAME= config('AWS_S3_SIGNATURE_NAME')
# AWS_SECRET_ACCESS_KEY= config('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME= config('AWS_STORAGE_BUCKET_NAME')
# AWS_DEFAULT_ACL = None
# AWS_S3_VERITY = config('AWS_S3_VERITY', default='True')
# AWS_S3_FILE_OVERWRITE = config('AWS_S3_FILE_OVERWRITE', default='False')

# For development, using console email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# # Email configuration
# EMAIL_BACKEND = config('EMAIL_BACKEND')
# EMAIL_HOST = config('EMAIL_HOST')
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# STORAGES = {
#     # Media files storage configuration
#     # 'default': {
#     #     'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
#     # },
    
#     # CSS and JS file management
#     'staticfiles': {
#         'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
#     },
# }

# Trusted origins
CSRF_TRUSTED_ORIGINS = []

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles', 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

# Media files 
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.UserAccount'

# Allauth Configuration
SITE_ID = 1
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_FIELDS = ['email']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_FORMS = {
    'login': 'accounts.forms.CustomLoginForm'
}

# Required allauth settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Redirect settings
LOGIN_REDIRECT_URL = '/accounts/profile/'
LOGIN_URL = '/accounts/login/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/login/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'  
ACCOUNT_LOGIN_ON_SIGNUP = False   
ACCOUNT_CHANGE_PASSWORD_REDIRECT_URL = '/accounts/login/'
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  

# Session settings
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True

OPENAI_API_KEY= config('OPENAI_API_KEY')