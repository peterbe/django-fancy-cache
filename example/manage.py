#!/usr/bin/env python
import os
import sys

# make sure we're running the fancy_cache here and not anything installed
parent = os.path.normpath(os.path.join(__file__, "../.."))
sys.path.insert(0, parent)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
