# -*- coding: utf-8 -*-
import os.path

PROJECT_NAME = 'Crime Corp'
SITE_DIR = 'crims'

MAINTANCE_MODE = False
IS_FB = False

if os.path.abspath(__file__).startswith('/Users/marekmikuliszyn/Sites/' + SITE_DIR):
    PROJECT_DIR = '/Users/marekmikuliszyn/Sites/' + SITE_DIR
    LOCAL = True
    DEBUG = True
else:
    PROJECT_DIR = '/home/marek/' + SITE_DIR
    LOCAL = False
    DEBUG = False

TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG
# INTERNAL_IPS = ('127.0.0.1', '94.78.183.198', '69.63.187.251')

SECRET_KEY = ''

if LOCAL:
    DATABASE_USER = 'root'
    DATABASE_PASSWORD = ''
else:
    DATABASE_USER = 'marek_remote'
    DATABASE_PASSWORD = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crims',
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': '',
        'PORT': '',
    },
}

DATABASE_OPTIONS = {
    'charset': 'utf8',
}

if LOCAL:
    SITE_ROOT_URL = 'http://192.168.1.2:8000/'
    MEDIA_URL = 'http://localhost/static/crims/'
    BASE_MEDIA_URL = 'http://localhost/static/base/'
else:
    SITE_ROOT_URL = 'http://www.crimecorp.com/'
    MEDIA_URL = 'http://static.crimecorp.com/'
    BASE_MEDIA_URL = 'http://static.madfb.com/base/'

MEDIA_ROOT = os.path.join(PROJECT_DIR, '..', 'static', 'crims') + '/'

ADMINS = (
    ('marek', ''),
)
MANAGERS = ADMINS
ADMIN_UIDS = ('1',)  # , '2')

TIME_ZONE = 'Europe/London'
# TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True
LANGUAGES = (
    ('en', 'English'),
    ('pl', 'Polish'),
    # ('de', 'German')
)
LANGUAGE_CODE = 'en-us'

ROOT_URLCONF = SITE_DIR + '.urls'
APPEND_SLASH = True
SITE_ID = 1

AUTH_PROFILE_MODULE = 'userprofile.userprofile'
# LOGIN_URL = ''
# LOGOUT_URL = ''
# LOGIN_REDIRECT_URL = ''

ACCOUNT_ACTIVATION_DAYS = 7

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = 'marek@madfb.com'

DATE_FORMAT = 'd/m/Y'

SESSION_COOKIE_NAME = SITE_DIR + '_cookie'
SESSION_COOKIE_AGE = 3600 * 24  # 24h
SESSION_COOKIE_AT_BROWSER_CLOSE = True

IS_FRAME = False

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# FILE_UPLOAD_HANDLERS = (
# 	'django.core.files.uploadhandler.TemporaryFileUploadHandler',
# )
# FILE_UPLOAD_TEMP_DIR = os.path.join(MEDIA_ROOT, 'upload')
# PHOTO_UPLOAD_DIR = 'photo'

if LOCAL:
    CACHE_BACKEND = 'dummy:///'
else:
    # CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=86400'
    # CACHE_BACKEND = 'db://django_cache?timeout=86400'
    CACHE_BACKEND = 'dummy:///'

SRPOINTS_SECRET = {
    'www': '',
    'fb': '',
}

OFFERPAL_SECRET = {
    'www': '',
    'fb': '',
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'crims.common.fb_connect.FacebookConnectMiddleware',
    'crims.common.middleware.engine.EngineMiddleware',
    # 'crims.common.middleware.ProfilerMiddleware',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.humanize',
    # 'django.contrib.flatpages',
    # --- External
    SITE_DIR + '.registration',
    # --- Crims
    SITE_DIR + '.common',
    SITE_DIR + '.userprofile',
    SITE_DIR + '.main',
    SITE_DIR + '.city',
    SITE_DIR + '.item',
    SITE_DIR + '.job',
    SITE_DIR + '.auction',
    SITE_DIR + '.gang',
    SITE_DIR + '.msg',
    # --- Internal
    SITE_DIR + '.intranet',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'crims.helpers.sql_debug.sqldebug',
    # SITE_DIR + '.common.context_processors.messages',
    SITE_DIR + '.common.context_processors.base',
    SITE_DIR + '.common.helpers.sql_debug.sqldebug',
)

from settings_game import *
