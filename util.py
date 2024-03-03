from common import logger
import requests_cache
import time
import diskcache
import pathlib
import tempfile
import contextlib


def run(f):
    return f()


class DefaultReprMixin:
    def __repr__(self):
        pieces = [
            '{}={}'.format(key, repr(data)) for key, data in self.__dict__.items()
        ]
        return '{}({})'.format(self.__class__.__name__, ', '.join(pieces))


requests_cache_session = requests_cache.CachedSession('.cache/http_cache.sqlite')


def web_get(url):
    """
    Perform a HTTP(S) GET and log if it wasn't cached.
    """
    is_cached = requests_cache_session.cache.contains(url=url)

    if not is_cached:
        start_time = time.time()
        logger.info(f'fetching {url} ...')

    ret = requests_cache_session.get(url)

    if not is_cached:
        logger.info(
            f'finished fetching {url} after {time.time() - start_time:.2f} seconds'
        )

    return ret


@contextlib.contextmanager
def web_get_to_file(url, binary=True, suffix=None):
    """
    Download a URL and write contents to a temporary file.

    This is a context manager that yields the temporary file path.
    """
    mode = 'w+b' if binary else 'w+'
    resp = web_get(url)
    if not binary:
        # Skip super-slow encoding detection by assuming content is utf8.
        # https://github.com/psf/requests/issues/2359
        resp.encoding = 'utf8'
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix) as f:
        f.write(resp.content if binary else resp.text)
        f.seek(0)
        yield f


# taken from https://docs.python.org/3/howto/logging-cookbook.html
class LoggingContext:
    def __init__(self, logger, level=None, handler=None, close=True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
        # implicit return of None => don't swallow exceptions


# See https://github.com/grantjenks/python-diskcache/issues/204
diskcache.core.DBNAME = 'computation_cache.db'
cache_on_disk = diskcache.Cache(
    directory=pathlib.Path(__file__).parent / '.cache'
).memoize()
