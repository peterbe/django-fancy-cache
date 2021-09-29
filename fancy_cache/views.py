from django.shortcuts import render
from django.conf import settings

from fancy_cache.memory import find_urls


def home(request):
    data = {
        "found": find_urls([]),
        "remember_all_urls_setting": getattr(
            settings, "FANCY_REMEMBER_ALL_URLS", False
        ),
        "remember_stats_all_urls_setting": getattr(
            settings, "FANCY_REMEMBER_STATS_ALL_URLS", False
        ),
    }
    return render(request, "fancy-cache/home.html", data)
