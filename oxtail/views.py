from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from urllib import urlencode
import os
from django.conf import settings

def get_file_contents(filename):
    file = open(filename)
    out = file.read()
    file.close
    return out

def raplet(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', '/gmail/media')
    }
    response = {
        'html': render_to_string('oxtail/poligraft.html'),
        'js': render_to_string('oxtail/poligraft.js', host),
        'css': render_to_string('oxtail/poligraft.css', host),
    }
    
    out = json.dumps(response)
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], out), 'text/javascript')
    else:
        return HttpResponse(out, mimetype="application/json")
