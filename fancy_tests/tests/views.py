import uuid
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from fancy_cache import cache_page


def _view(request):
    random_string = uuid.uuid4().hex
    return render(request, "home.html", dict(random_string=random_string))


@cache_page(60)
def home(request):
    return _view(request)


def prefixer1(request):
    if request.META.get("AUTH_USER"):
        # disable
        return None
    return "a_key"


@cache_page(60, key_prefix=prefixer1)
def home2(request):
    return _view(request)


def post_processor1(response, request):
    assert "In your HTML" not in response.content.decode("utf8")
    response.content += ("In your HTML:%s" % uuid.uuid4().hex).encode("utf8")
    return response


@cache_page(60, key_prefix=prefixer1, post_process_response=post_processor1)
def home3(request):
    return _view(request)


@cache_page(
    60, key_prefix=prefixer1, post_process_response_always=post_processor1
)
def home4(request):
    return _view(request)


@cache_page(60, only_get_keys=["foo", "bar"])
def home5(request):
    return _view(request)


@cache_page(60, forget_get_keys=["bar"])
def home5bis(request):
    return _view(request)


@cache_page(60, remember_stats_all_urls=True, remember_all_urls=True)
def home6(request):
    return _view(request)


@cache_page(60, cache="second_backend")
def home7(request):
    return _view(request)


@cache_page(60, cache="dummy_backend", remember_all_urls=True)
def home8(request):
    return _view(request)


@never_cache
@cache_page(60, remember_stats_all_urls=True, remember_all_urls=True)
def home9(request):
    return _view(request)
