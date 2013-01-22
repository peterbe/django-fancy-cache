import re
from nose.tools import eq_, ok_
from django.test.client import RequestFactory
from django.conf import settings

from . import views


def test_render_home1():
    factory = RequestFactory()
    request = factory.get('/')

    response = views.home(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_1 = re.findall('Random:(\w+)', response.content)[0]

    # do it again
    response = views.home(request)
    eq_(response.status_code, 200)
    random_string_2 = re.findall('Random:(\w+)', response.content)[0]
    eq_(random_string_1, random_string_2)


def test_render_home2():
    factory = RequestFactory()
    authenticated = RequestFactory(AUTH_USER='peter')
    request = factory.get('/2')

    response = views.home2(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_1 = re.findall('Random:(\w+)', response.content)[0]

    # do it again
    response = views.home2(request)
    eq_(response.status_code, 200)
    random_string_2 = re.findall('Random:(\w+)', response.content)[0]
    eq_(random_string_1, random_string_2)

    # do it again, but with a hint to disable cache
    request = authenticated.get('/2')
    response = views.home2(request)
    eq_(response.status_code, 200)
    random_string_2 = re.findall('Random:(\w+)', response.content)[0]
    ok_(random_string_1 != random_string_2)


def test_render_home3():
    factory = RequestFactory()
    request = factory.get('/3')

    response = views.home3(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_1 = re.findall('Random:(\w+)', response.content)[0]
    ok_('In your HTML' in response.content)
    extra_random_string_1 = re.findall('In your HTML:(\w+)', response.content)[0]

    response = views.home3(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_2 = re.findall('Random:(\w+)', response.content)[0]
    extra_random_string_2 = re.findall('In your HTML:(\w+)', response.content)[0]
    ok_('In your HTML' in response.content)
    eq_(random_string_1, random_string_2)
    # the post_process_response is only called once
    eq_(extra_random_string_1, extra_random_string_2)


def test_render_home3_no_cache():
    factory = RequestFactory(AUTH_USER='peter')
    request = factory.get('/3')

    response = views.home3(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    ok_('In your HTML' not in response.content)


def test_render_home4():
    factory = RequestFactory()
    request = factory.get('/4')

    response = views.home4(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_1 = re.findall('Random:(\w+)', response.content)[0]
    ok_('In your HTML' in response.content)
    extra_random_string_1 = re.findall('In your HTML:(\w+)', response.content)[0]

    response = views.home4(request)
    eq_(response.status_code, 200)
    ok_(re.findall('Random:\w+', response.content))
    random_string_2 = re.findall('Random:(\w+)', response.content)[0]
    extra_random_string_2 = re.findall('In your HTML:(\w+)', response.content)[0]
    ok_('In your HTML' in response.content)
    eq_(random_string_1, random_string_2)
    # the post_process_response is now called every time
    ok_(extra_random_string_1 != extra_random_string_2)
