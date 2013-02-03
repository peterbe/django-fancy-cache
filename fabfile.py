"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import os

from fabric.api import local


ROOT = os.path.abspath(os.path.dirname(__file__))
os.environ['PYTHONPATH'] = ROOT


def _test(extra_args):
    """Run test suite."""
    os.environ['DJANGO_SETTINGS_MODULE'] = 'fancy_tests.tests.settings'
    os.environ['REUSE_DB'] = '0'

    # Add tables and flush DB
    local('django-admin.py syncdb --noinput')
    local('django-admin.py flush --noinput')

    local('django-admin.py test %s' % extra_args)

def test():
    _test('-s')

def coverage():
    _test('-s --with-coverage --cover-erase --cover-html '
          '--cover-package=fancy_cache')
