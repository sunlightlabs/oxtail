from django.conf.urls.defaults import *
import os

urlpatterns = patterns('',
    url(r'^rapportive.json$', 'oxtail.views.raplet', name='raplet'),
    url(r'^oxtail.js$', 'oxtail.views.oxtail_js', name='oxtail_js'),
    url(r'^person_info.json$', 'oxtail.views.person_info', name='oxtail_person_info'),
    
    url(r'^oxtail.crx$', 'oxtail.views.oxtail_crx', name='oxtail_crx'),
    url(r'^oxtail.xpi$', 'oxtail.views.oxtail_xpi', name='oxtail_xpi'),
    
    url(r'^pg_proxy$', 'oxtail.views.pg_proxy', name='pg_proxy'),
    
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.dirname(__file__) + '/media'}),
    
    url(r'^$', 'oxtail.views.index', name='oxtail_index'),
)
