import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = 'anything'

ALLOWED_HOSTS = ()

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

#TEMPLATE_DIRS = (
#    os.path.join(HERE, 'templates'),
#)

INSTALLED_APPS = (
    'fancy_cache',
    'fancy_tests.tests',  # Needed??
    #'django_nose',
)


ROOT_URLCONF = 'fancy_tests.tests.urls'

# XXX not sure which if these we need at all
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
