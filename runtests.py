import os
import sys

import django
from django.test.utils import get_runner
from django.conf import settings


def runtests():
    test_dir = os.path.join(os.path.dirname(__file__), 'fancy_tests/tests')
    sys.path.insert(0, test_dir)

    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False, failfast=False)
    failures = test_runner.run_tests(['fancy_tests.tests'])

    sys.exit(bool(failures))


if __name__ == '__main__':
    runtests()
