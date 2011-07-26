from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import os

urlpatterns = patterns('',
    url(r'^rapportive.json$', 'oxtail.views.raplet', name='raplet'),
    url(r'^oxtail.js$', 'oxtail.views.oxtail_js', name='oxtail_js'),
    
    url(r'^oxtail.crx$', 'oxtail.views.oxtail_crx', name='oxtail_crx'),
    url(r'^oxtail.xpi$', 'oxtail.views.oxtail_xpi', name='oxtail_xpi'),
    url(r'^update.rdf$', 'oxtail.views.oxtail_xpi_update', name='oxtail_xpi_update'),
    url(r'^update.xml$', 'oxtail.views.oxtail_crx_update', name='oxtail_xpi_update'),
        
    url(r'^contextualize$', 'oxtail.views.contextualize_text', name='contextualize'),
    url(r'^sender_info$', 'oxtail.views.sender_info', name='sender_info'),
    
    url(r'^entity/(?P<id>\w+)$', 'oxtail.views.entity_info', name='oxtail_entity_info'),
    
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.dirname(__file__) + '/media'}, name="oxtail_media"),
    
    url(r'^api/$', direct_to_template, {'template': 'oxtail/api.html'}),
    url(r'^$', 'oxtail.views.index', name='oxtail_index'),
)
