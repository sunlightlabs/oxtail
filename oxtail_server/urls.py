from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    # evil url for media.
    url(r'^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'), 
        'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
    (r'', include('oxtail.urls')),
)
