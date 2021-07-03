.. index:: gettingstarted

.. _gettingstarted-chapter:

Getting started
===============

The minimal you need to do is install ``django-fancy-cache`` and add
it to a view.

Installing is easy::

    $ pip install django-fancy-cache

Now, let's assume you have a ``views.py`` that looks like this::

    from django.shortcuts import render

    def my_view(request):
        something_really_slow...
	return render(request, 'template.html')


What you add is this::

    from django.shortcuts import render
    from fancy_cache import cache_page

    @cache_page(3600)
    def my_view(request):
        something_really_slow...
	return render(request, 'template.html')


Fancy cache also works for Class-based Views with the help of [Django's `method_decorator`](https://docs.djangoproject.com/en/dev/topics/class-based-views/intro/#decorating-the-class)::

    from django.utils.decorators import method_decorator
    from django.views.generic import TemplateView
    from fancy_cache import cache_page


    class MyView(TemplateView):
        template_name = "template.html"

        @method_decorator(cache_page(3600))
        def get(self, request, *args, **kwargs):
            return super().get(request, *args, **kwargs)


Getting fancy
-------------

The above stuff isn't particularly fancy. The next steps is to
start :ref:`gettingfancy-chapter`.
