.. index:: changelog

.. _changelog-chapter:

Changelog
=========

1.1.0
-------------------

* If you use Memcached you can set
  ``settings.FANCY_USE_MEMCACHED_CHECK_AND_SET = True`` so that you
  can use ``cache._cache.cas`` which only workd with Memcached.

1.0.0
-------------------

* Drop support for Python <3.5 and Django <2.2.0

0.11.0
-------------------

* Fix for ``parse_qs`` correctly between Python 2 and Python 3

0.10.0
-------------------

* Fix for keeping blank strings in query strings. #39

0.9.0
-------------------

* Django 1.10 support

0.8.2
-------------------

* Remove deprecated way to define URL patterns and tests in python 3.5

0.8.1
-------------------

* Ability to specify different cache backends to be used
  https://github.com/peterbe/django-fancy-cache/pull/31

0.8.0
-------------------

* Started keeping a Changelog

v0.4.0 (2013-03-12)
-------------------

The function ``fancy_cache.memory.find_urls()`` can now be called
without any arguments since means it matches *all* URLs.

If you enable ``FANCY_REMEMBER_STATS_ALL_URLS`` and have some really
big URLs (e.g. long query strings) you could get
``MemcachedKeyLengthError`` errors potentially.

v0.3.2 (2013-02-13)
-------------------

Small improvement to the example app, documentation and a bunch of
commented out debugging removed.

v0.3.1 (2013-02-11)
-------------------

Docs added.

v0.3 (2013-02-11)
-----------------

First time a changelog is started.
