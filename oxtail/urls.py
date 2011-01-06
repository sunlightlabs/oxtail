from django.conf.urls.defaults import *
import os

urlpatterns = patterns('',
    url(r'^rapportive.json$', 'oxtail.views.raplet', name='raplet'),
    url(r'^test.js$', 'oxtail.views.test_js', name='test'),
    
    url(r'^pg_proxy$', 'oxtail.views.pg_proxy', name='pg_proxy'),
    
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.dirname(__file__) + '/media'}),
)
