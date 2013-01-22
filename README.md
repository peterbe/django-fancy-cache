django-fancy-cache
==================

(c) Peter Bengtsson, mail@peterbe.com, 2013

About django-fancy-cache
------------------------

A Django `cache_page` decorator on steroids.

Unlike the stock `django.views.decorators.cache.change_page` this
decorator makes it possible to set a `key_prefixer` that is a
callable. This callable is passed the request and if it returns `None`
the page is not cached.

Also, you can set another callable called `post_process_response`
(which is passed the response and the request) which can do some
additional changes to the response before it's set in cache.

Lastly, you can set `post_process_response_always=True` so that the
`post_process_response` callable is always called, even when the
response is coming from the cache.


How to use it
-------------

In your Django views:

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


Running the test suite
----------------------

The simplest way is to simply run:

        $ pip install -r requirements.txt
        $ fab test

Or to run it without `fab` you can simply run:

        $ export PYTHONPATH=`pwd`
	$ export DJANGO_SETTINGS_MODULE=fancy_cache.tests.settings
	$ django-admin.py test
