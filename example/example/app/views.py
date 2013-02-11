import time

from django.shortcuts import render, redirect

from fancy_cache import cache_page
from fancy_cache.memory import find_urls


def home(request):
    remembered_urls = find_urls([])
    return render(
        request,
        'home.html',
        {'remembered_urls': remembered_urls}
    )


def commafy(s):
    r = []
    for i, c in enumerate(reversed(str(s))):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    return ''.join(r)


@cache_page(60)
def page1(request):
    print "CACHE MISS", request.build_absolute_uri()
    t0 = time.time()
    result = sum(x for x in xrange(25000000))
    t1 = time.time()
    print t1 - t0
    return render(
        request,
        'page.html',
        dict(result=commafy(result), page='1')
    )


def key_prefixer(request):
    # if it's not there, don't cache
    return request.GET.get('number')


@cache_page(60, key_prefix=key_prefixer)
def page2(request):
    if not request.GET.get('number'):
        return redirect(request.build_absolute_uri() + '?number=25000000')
    print "CACHE MISS", request.build_absolute_uri()
    t0 = time.time()
    result = sum(x for x in xrange(25000000))
    t1 = time.time()
    print t1 - t0
    return render(
        request,
        'page.html',
        dict(result=commafy(result), page='2')
    )


def post_processor(response, request):
    response.content = response.content.replace(
        '</body>',
        '<footer>Kilroy was here!</footer></body>'
    )
    return response


@cache_page(60, post_process_response=post_processor)
def page3(request):
    print "CACHE MISS", request.build_absolute_uri()
    t0 = time.time()
    result = sum(x for x in xrange(25000000))
    t1 = time.time()
    print t1 - t0
    return render(
        request,
        'page.html',
        dict(result=commafy(result), page='3')
    )


def post_processor_always(response, request):
    import datetime
    now = datetime.datetime.now()
    assert 'Right here right now' not in response.content, 'already there!'
    response.content = response.content.replace(
        '</body>',
        '<footer>Right here right now %s</footer></body>' % now
    )
    return response


@cache_page(60, post_process_response_always=post_processor_always)
def page4(request):
    print "CACHE MISS", request.build_absolute_uri()
    t0 = time.time()
    result = sum(x for x in xrange(25000000))
    t1 = time.time()
    print t1 - t0
    return render(
        request,
        'page.html',
        dict(result=commafy(result), page='4')
    )


@cache_page(60, only_get_keys=['foo', 'bar'])
def page5(request):
    print "CACHE MISS", request.build_absolute_uri()
    t0 = time.time()
    result = sum(x for x in xrange(25000000))
    t1 = time.time()
    print t1 - t0
    return render(
        request,
        'page.html',
        dict(result=commafy(result), page='5')
    )
