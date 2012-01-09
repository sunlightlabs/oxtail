__extension_version__ = '0.4.4'

import subprocess, os
git = subprocess.Popen('cd %s; git log -n 1 --raw --oneline' % os.path.dirname(os.path.abspath(__file__)), shell=True, stdout=subprocess.PIPE)
out, err = git.communicate()
__git_rev__ = out.split(' ')[0]

__all__ = ['__version__', '__git_rev__']

# monkey-patch Locksmith's API key model to use local caching
try:
    from oxtail.util import cache as cache_func
    from locksmith.auth.models import ApiKey
    ApiKey.objects.get = cache_func(3600)(ApiKey.objects.get)
except ImportError:
    pass
