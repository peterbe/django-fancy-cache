import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'anything'

ALLOWED_HOSTS = ('testserver',)

DATABASES = {
    'default': {
        'NAME': ':memory:',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

INSTALLED_APPS = [
    'fancy_cache',
    'fancy_tests.tests',

    'django.contrib.auth',
    'django.contrib.contenttypes',
]


ROOT_URLCONF = 'fancy_tests.tests.urls'
