import os
HERE = os.path.dirname(__file__)

TEST_RUNNER = 'django_nose.runner.NoseTestSuiteRunner'

SECRET_KEY = 'anything'

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

TEMPLATE_DIRS = (
    os.path.join(HERE, 'templates'),
)

INSTALLED_APPS = (
    'fancy_cache',
    'django_nose',
)


ROOT_URLCONF = 'fancy_cache.tests.urls'
