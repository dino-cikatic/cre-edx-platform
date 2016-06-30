"""
Helper functions for caching course assets.
"""
from django.core.cache import get_cache
from opaque_keys import InvalidKeyError

CONTENTSERVER_VERSION=1

# See if there's a "course_assets" cache configured, and if not, fallback to the default cache.
try:
    cache = get_cache('course_assets')
except:
    cache = get_cache('default')


def set_cached_content(content):
    """
    Stores the given piece of content in the cache, using its location as the key.
    """
    cache.set(unicode(content.location).encode("utf-8"), content, version=CONTENTSERVER_VERSION)


def get_cached_content(location):
    """
    Retrieves the given piece of content by its location if cached.
    """
    return cache.get(unicode(location).encode("utf-8"), version=CONTENTSERVER_VERSION)


def del_cached_content(location):
    """
    Delete content for the given location, as well versions of the content without a run.

    It's possible that the content could have been cached without knowing the course_key,
    and so without having the run.
    """
    def location_str(loc):
        return unicode(loc).encode("utf-8")

    locations = [location_str(location)]
    try:
        locations.append(location_str(location.replace(run=None)))
    except InvalidKeyError:
        # although deprecated keys allowed run=None, new keys don't if there is no version.
        pass

    cache.delete_many(locations, version=CONTENTSERVER_VERSION)
