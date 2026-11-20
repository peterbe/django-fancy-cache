import codecs
import os
import re


# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup, find_packages


def read(*parts):
    content = codecs.open(
        os.path.join(os.path.dirname(__file__), *parts)
    ).read()
    try:
        return content.decode("utf8")
    except AttributeError:
        # python 3
        return content


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="django-fancy-cache",
    version=find_version("fancy_cache/__init__.py"),
    description="A Django 'cache_page' decorator on steroids",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    author="Peter Bengtsson",
    author_email="mail@peterbe.com",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Framework :: Django :: 6.1",
    ],
    python_requires=">=3.10",
    url="https://github.com/peterbe/django-fancy-cache",
)
