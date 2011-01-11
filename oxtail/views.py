from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from urllib import urlencode
import os
import urllib2
from django.conf import settings
from oxtail.decorators import cors_allow_all
from django.views.generic.simple import direct_to_template


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

def index(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path': getattr(settings, 'OXTAIL_PATH', '/gmail'),
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', '/gmail/media')
    }
    
    return direct_to_template(request, 'oxtail/index.html', extra_context=host)


# Browser extension code
from oxtail.extension import UserScriptExtension
class OxtailExtension(UserScriptExtension):
    name = 'Oxtail'
    version = '0.1'
    description = 'Oxtail implemented as a Chrome extension.'
    matches = [
        "http://mail.google.com/mail*",
        "https://mail.google.com/mail*",
        "http://mail.google.com/a/*",
        "https://mail.google.com/a/*"
    ]
    
    pem_path = os.path.join(os.path.dirname(__file__), 'oxtail.pem')
    
    def __init__(self, host, oxtail_path):
        self.host = host
        self.oxtail_path = oxtail_path
    
    def get_user_script(self):
        host = {
            'host' : 'http://%s' % self.host,
            'oxtail_path': self.oxtail_path,
        }
        return render_to_string('oxtail/crx.js', host)

def oxtail_crx(request):
    extension = OxtailExtension(request.META['HTTP_HOST'], getattr(settings, 'OXTAIL_PATH', '/gmail'))
    response = HttpResponse(mimetype='application/x-chrome-extension')
    extension.gen_crx(response)
    return response