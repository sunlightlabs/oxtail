# taken from http://djangosnippets.org/snippets/564/

from hashlib import sha1
from django.core.cache import cache as _djcache
def cache(seconds = 900):
    def doCache(f):
        def x(*args, **kwargs):
                key = sha1(str(f.__module__) + str(f.__name__) + str(args) + str(kwargs)).hexdigest()
                result = _djcache.get(key)
                if result is None:
                    result = f(*args, **kwargs)
                    _djcache.set(key, result, seconds)
                return result
        return x
    return doCache

def is_int(val):
    try:
        dummy = int(val)
        return True
    except ValueError:
        return False

seat_labels = {'federal:senate': 'US Senate',
               'federal:house': 'US House',
               'federal:president': 'President',
               'state:upper': 'State Upper Chamber',
               'state:lower': 'State Lower Chamber',
               'state:governor': 'Governor',
               'state:ltgovernor': 'Lt. Governor',
               'state:judicial': 'State Judiciary',
               'state:office': 'Other State Office'
               }
