django-fancy-cache
==================

Copyright Peter Bengtsson, mail@peterbe.com, 2013-2016

|Travis|

License: BSD

About django-fancy-cache
------------------------

A Django ``cache_page`` decorator on steroids.

Unlike the stock ``django.views.decorators.cache.change_page`` this
decorator makes it possible to set a ``key_prefixer`` that is a
callable. This callable is passed the request and if it returns ``None``
the page is not cached.

Also, you can set another callable called ``post_process_response``
(which is passed the response and the request) which can do some
additional changes to the response before it's set in cache.

Lastly, you can set ``post_process_response_always=True`` so that the
``post_process_response`` callable is always called, even when the
response is coming from the cache.


How to use it
-------------

In your Django views:

.. code:: python

    from fancy_cache import cache_page

    @cache_page(60 * 60)
    def myview(request):
        return render(request, 'page1.html')

    def prefixer(request):
        if request.method != 'GET':
            return None
        if request.GET.get('no-cache'):
            return None
        return 'myprefix'

    @cache_page(60 * 60, key_prefixer=prefixer)
    def myotherview(request):
        return render(request, 'page2.html')

    def post_processor(response, request):
        response.content += '<!-- this was post processed -->'
        return response

    @cache_page(60 * 60,
                key_prefixer=prefixer,
            post_process_response=post_processor)
    def yetanotherotherview(request):
        return render(request, 'page3.html')

Optional uses
-------------

If you want to you can have ``django-fancy-cache`` record every URL it
caches. This can be useful for things like invalidation or curious
statistical inspection.

You can either switch this on on the decorator itself. Like this:

.. code:: python

    from fancy_cache import cache_page

    @cache_page(60 * 60, remember_all_urls=True)
    def myview(request):
        return render(request, 'page1.html')

Or, more conveniently to apply it to all uses of the ``cache_page``
decorator you can set the default in your settings with:

.. code:: python

    FANCY_REMEMBER_ALL_URLS = True

Now, suppose you have the this option enabled. Now you can do things
like this:

.. code:: python

    >>> from fancy_cache.memory import find_urls
    >>> list(find_urls(['/some/searchpath', '/or/like/*/this.*']))
    >>> # or, to get all:
    >>> list(find_urls([]))

There is also another option to this and that is to purge (aka.
invalidate) the remembered URLs. You simply all the ``purge=True``
option like this:

.. code:: python

    >>> from fancy_cache.memory import find_urls
    >>> list(find_urls([], purge=True))

Note: Since ``find_urls()`` returns a generator, the purging won't
happen unless you exhaust the generator. E.g. looping over it or
turning it into a list.

The second way to inspect all recorded URLs is to use the
``fancy-cache`` management command. This is only available if you have
added ``fancy_cache`` to your ``INSTALLED_APPS`` setting. Now you can do
this::

    $ ./manage.py fancy-cache --help
    $ ./manage.py fancy-cache
    $ ./manage.py fancy-cache /some/searchpath /or/like/*/this.*
    $ ./manage.py fancy-cache /some/place/* --purge
    $ # or to purge them all!
    $ ./manage.py fancy-cache --purge

Note, it will only print out URLs that if found (and purged, if
applicable).

The third way to inspect the recorded URLs is to add this to your root
``urls.py``:

.. code:: python

    url(r'fancy-cache', include('fancy_cache.urls')),

Now, if you visit ``http://localhost:8000/fancy-cache`` you get a table
listing every URL that ``django-fancy-cache`` has recorded.


Optional uses (for the exceptionally curious)
---------------------------------------------

If you have enabled ``FANCY_REMEMBER_ALL_URLS`` you can also enable
``FANCY_REMEMBER_STATS_ALL_URLS`` in your settings. What this does is
that it attempts to count the number of cache hits and cache misses
you have for each URL.

This counting of hits and misses is configured to last "a long time".
Possibly longer than you cache your view. So, over time you can expect
to have more than one miss because your view cache expires and it
starts over.

You can see the stats whenever you use any of the ways described in
the section above. For example like this:

.. code:: python

    >>> from fancy_cache.memory import find_urls
    >>> found = list(find_urls([]))[0]
    >>> found[0]
    '/some/page.html'
    >>> found[2]
    {'hits': 1235, 'misses': 12}

There is obviously a small additional performance cost of using the
``FANCY_REMEMBER_ALL_URLS`` and/or ``FANCY_REMEMBER_STATS_ALL_URLS`` in
your project so only use it if you don't have any smarter way to
invalidate, for debugging or if you really want make it possible to
purge all cached responses when you run an upgrade of your site or
something.

Running the test suite
----------------------

The simplest way is to simply run::

    $ pip install tox
    $ tox

Or to run it without ``tox`` you can simply run::

    $ export PYTHONPATH=`pwd`
    $ export DJANGO_SETTINGS_MODULE=fancy_tests.tests.settings
    $ django-admin.py test


.. |Travis| image:: https://travis-ci.org/peterbe/django-fancy-cache.png?branch=master
   :target: https://travis-ci.org/peterbe/django-fancy-cache


Changelog
---------

(Sorry, been poor in maintaining this. Let's get it right from now)

1.0.0
    * Drop support for Python <3.5 and Django <2.2.0

0.11.0
    * Fix for ``parse_qs`` correctly between Python 2 and Python 3

0.10.0
    * Fix for keeping blank strings in query strings. #39

0.9.0
    * Django 1.10 support

0.8.2
    * Remove deprecated way to define URL patterns and tests in python 3.5

0.8.1
    * Ability to specify different cache backends to be used
      https://github.com/peterbe/django-fancy-cache/pull/31

0.8.0
    * Started keeping a Changelog
