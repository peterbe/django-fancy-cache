from __future__ import print_function
import os

_this_wo_ext = os.path.basename(__file__).rsplit(".", 1)[0]

__doc__ = """
If you enable `FANCY_REMEMBER_ALL_URLS` then every URL take is turned
into a cache key for cache_page() to remember is recorded.
You can use this to do statistics or to do invalidation by URL.

To use: simply add the URL patterns after like this::

    $ ./manage.py %(this_file)s /path1.html /path3/*/*.json

To show all cached URLs simply run it with no pattern like this::

    $ ./manage.py %(this_file)s

Equally the ``--purge`` switch can always be added. For example,
running this will purge all cached URLs::

    $ ./manage.py %(this_file)s --purge

If you enable `FANCY_REMEMBER_STATS_ALL_URLS` you can get a tally for each
URL how many cache HITS and MISSES it has had.

""" % dict(
    this_file=_this_wo_ext
)

from optparse import make_option

from django.core.management.base import BaseCommand

from fancy_cache.memory import find_urls


class Command(BaseCommand):
    help = __doc__.strip()

    def add_arguments(self, parser):
        parser.add_argument(
            "-p",
            "--purge",
            dest="purge",
            action="store_true",
            help="Purge found URLs",
        )

    args = "urls"

    def handle(self, *urls, **options):
        verbose = int(options["verbosity"]) > 1
        _count = 0
        for url, cache_key, stats in find_urls(urls, purge=options["purge"]):
            _count += 1
            if stats:
                self.stdout.write(url[:70].ljust(65)),
                self.stdout.write("HITS", str(stats["hits"]).ljust(5)),
                self.stdout.write("MISSES", str(stats["misses"]).ljust(5))

            else:
                self.stdout.write(url)

        if verbose:
            self.stdout.write("-- %s URLs cached --" % _count)
