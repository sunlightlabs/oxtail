from django.conf.urls.defaults import *
import os

urlpatterns = patterns('',
    url(r'^rapportive.json$', 'oxtail.views.raplet', name='raplet'),
    url(r'^oxtail.js$', 'oxtail.views.oxtail_js', name='oxtail_js'),
    url(r'^oxtail.crx$', 'oxtail.views.oxtail_crx', name='oxtail_crx'),
    
    url(r'^pg_proxy$', 'oxtail.views.pg_proxy', name='pg_proxy'),
    
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.dirname(__file__) + '/media'}),
    
    url(r'^$', 'oxtail.views.index', name='oxtail_index'),
)