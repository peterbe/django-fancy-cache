import uuid
from django.shortcuts import render
from fancy_cache import cache_page


def _view(request):
    random_string = uuid.uuid4().hex
    return render(request, 'home.html', dict(random_string=random_string))

@cache_page(60)
def home(request):
    return _view(request)


def prefixer1(request):
    if request.META.get('AUTH_USER'):
        # disable
        return None
    return 'a_key'

@cache_page(60, key_prefix=prefixer1)
def home2(request):
    return _view(request)


def post_processor1(response, request):
    response.content += 'In your HTML:%s' % uuid.uuid4().hex
    return response

@cache_page(60,
            key_prefix=prefixer1,
            post_process_response=post_processor1)
def home3(request):
    return _view(request)


@cache_page(60,
            key_prefix=prefixer1,
            post_process_response=post_processor1,
            post_process_response_always=True)
def home4(request):
    return _view(request)
