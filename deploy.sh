#!/bin/bash
set -e

rm -fr dist/*
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*
