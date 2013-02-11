.. index:: stats

.. _stats-chapter:

Stats - hits and misses
=======================

In :ref:`gettingfancy-chapter` we went through various ways of using
``django-fancy-cache`` that all have a functional difference.

What you can do is enable stats so you can get an insight into what
``django-fancy-cache`` does for you.

Setting up
----------

The first step is to switch on a setting. Put this in your
``settings``::

    FANCY_REMEMBER_ALL_URLS = True
    FANCY_REMEMBER_STATS_ALL_URLS = True

The other thing you need to do is to add ``fancy_cache`` to
``INSTALLED_APPS`` like this::

    INSTALLED_APPS += ('fancy_cache',)

The first one is to tell ``django-fancy-cache`` to remember every URL
it caches and the second one is to keep track of how many hits and
misses you have per URL.

This will enable stats collections on all uses of the ``cache_page``
decorator. Alternatively you can do it explicitely on just one view.
Like this::

    from django.shortcuts import render
    from fancy_cache import cache_page

    @cache_page(3600,
                remember_all_urls=True,
                remember_stats_all_urls=True)
    def my_view(request):
        something_really_slow...
	return render(request, 'template.html')


Now, run your view a couple of times and then you can use the
management command to get an output of this::

    $ ./manage.py fancy-urls
    /page5.html                                             HITS 62    MISSES 5
    /page4.html                                             HITS 4     MISSES 1

Another way add ``django-fancy-cache`` to your root urls.py like this::

    urlpatterns = patterns(
        '',
        ...your other stuff...,
        url(r'fancy-cache', include('fancy_cache.urls')),
    )


Now you can visit ``http://localhost:8000/fancy-cache``. It'll give
you a very basic table with all cache keys, their hits and misses.
