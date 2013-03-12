.. index:: changelog

.. _changelog-chapter:

Changelog
=========

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
