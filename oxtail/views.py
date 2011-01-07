from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from urllib import urlencode
import os
import urllib2
from django.conf import settings
from oxtail.decorators import cors_allow_all

def get_file_contents(filename):
    file = open(filename)
    out = file.read()
    file.close
    return out

def raplet(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path': getattr(settings, 'OXTAIL_PATH', '/gmail'),
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', '/gmail/media')
    }
    response = {
        'html': render_to_string('oxtail/poligraft.html', host),
        'js': '',
        'css': '',
    }
    
    out = json.dumps(response)
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], out), 'text/javascript')
    else:
        return HttpResponse(out, mimetype="application/json")

def oxtail_js(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path': getattr(settings, 'OXTAIL_PATH', '/gmail'),
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', '/gmail/media')
    }
    
    js = "\n".join([
        get_file_contents('%s/media/js/jquery-1.4.4.min.js' % os.path.dirname(__file__)),
        'jQuery.noConflict();',
        get_file_contents('%s/media/js/jquery.windowname.plugin.js' % os.path.dirname(__file__)),
        render_to_string('oxtail/poligraft.js', host)
    ])
    
    return HttpResponse(js, 'text/javascript')

@cors_allow_all
def pg_proxy(request):
    qs = request.META.get('QUERY_STRING', '')
    qs = '?%s' % qs if qs else qs
    
    url_kwargs = {}
    if request.method == 'POST':
        url_kwargs['data'] = request.raw_post_data
    
    resource = urllib2.urlopen('http://poligraft.com/poligraft', **url_kwargs)
    return HttpResponse(resource.read())
