from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from urllib import urlencode
import os
import urllib, urllib2
import base64
import string
from django.conf import settings
from oxtail.decorators import cors_allow_all
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from dbpedia import *
from itertools import groupby
from oxtail import matching

from oxtail.tasks import *

from django.conf import settings
from influence.api import api


def get_file_contents(filename):
    file = open(filename)
    out = file.read()
    file.close
    return out

def raplet(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path': reverse('oxtail_index')[:-1],
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', os.path.join(reverse('oxtail_index'), 'media'))
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
        'oxtail_path': reverse('oxtail_index')[:-1],
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', os.path.join(reverse('oxtail_index'), 'media'))
    }
    
    js = "\n".join([
        get_file_contents('%s/media/js/jquery-1.4.4.min.js' % os.path.dirname(__file__)),
        'jQuery.noConflict();',
        get_file_contents('%s/media/js/jquery.windowname.plugin.js' % os.path.dirname(__file__)),
        render_to_string('oxtail/poligraft.js', host)
    ])
    
    return HttpResponse(js, 'text/javascript')

def index(request):
    host = {
        'host' : 'http://%s' % request.META['HTTP_HOST'],
        'oxtail_path': reverse('oxtail_index')[:-1],
        'oxtail_media_path' : getattr(settings, 'OXTAIL_MEDIA_PATH', os.path.join(reverse('oxtail_index'), 'media'))
    }
    
    return direct_to_template(request, 'oxtail/index.html', extra_context=host)

@cors_allow_all
def contextualize_text(request, pg_id=None):
    text = request.REQUEST.get('text', '').strip()
    
    full_text = str(filter(lambda x: x in string.printable, text))
    
    matches = matching.match(full_text)
    
    out = {'entities': []}
    for match in matches:
        entity_data = get_entity_data(match)
        if not entity_data:
            continue
        out['entities'].append({
            'matched_text': list(matches[match]),
            'entity_data': entity_data
        })
            
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], json.dumps(out)), 'text/javascript')
    else:
        return HttpResponse(json.dumps(out), mimetype="application/json")

def entity_info(request, id):
    return HttpResponse(json.dumps(get_entity_data(id)), mimetype="application/json")

def sender_info(request):
    name = request.REQUEST.get('name', '').strip()
    email = request.REQUEST.get('email', '').strip()
    organization = None
    
    out = {}
    
    organization = ''
    org_info = None
    if email:
        parts = email.split("@")
        if len(parts) > 1:
            domain = parts[1]
            orgs = lookup_domain(domain)
            if orgs:
                organization = orgs[0]['name']
                matches = matching.match(organization)
                if matches:
                    org_info = get_entity_data(matches.keys()[0])
    
    results = None
    if name and organization:
        results = api._get_url_json('contributions.json', parse_json=True, contributor_ft=name, organization_ft=organization)
    
    if name and not results:
        results = api._get_url_json('contributions.json', parse_json=True, contributor_ft=name)
    
    sender_info = []
    if results:
        keyfunc = lambda r: (r['contributor_city'], r['contributor_state'])
        results = sorted(results, key=keyfunc)
        for location, result_iter in groupby(results, key=keyfunc):
            result = list(result_iter)
            sender_info.append({
                'city': string.capwords(location[0]),
                'state': location[1].upper(),
                'total': sum([float(r['amount']) for r in result]),
                'dem_total': sum([float(r['amount']) for r in result if r['recipient_party'] == 'D']),
                'rep_total': sum([float(r['amount']) for r in result if r['recipient_party'] == 'R']),
                'count': len(result),
                'url': base64.b64encode(urllib.urlencode({'contributor_ft': name, 'contributor_state': location[1].upper()}))
            })
    
    out = {
        'name': name,
        'email': email,
        'sender_info': sender_info,
        'url': base64.b64encode(urllib.urlencode({'contributor_ft': name})),
        'organization': organization,
        'org_info': org_info
    }
    
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], json.dumps(out)), 'text/javascript')
    else:
        return HttpResponse(json.dumps(out), mimetype="application/json")

# Browser extension code
from oxtail.extension import UserScriptExtension
class OxtailExtension(UserScriptExtension):
    id = 'oxtail@sunlightfoundation.com'
    name = 'Oxtail'
    version = '0.2'
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
        self.description = '%s (%s)' % (self.description, host)
    
    def get_user_script(self):
        host = {
            'host' : 'http://%s' % self.host,
            'oxtail_path': self.oxtail_path,
        }
        return render_to_string('oxtail/crx.js', host)

def oxtail_crx(request):
    extension = OxtailExtension(request.META['HTTP_HOST'], reverse('oxtail_index')[:-1])
    response = HttpResponse(mimetype='application/x-chrome-extension')
    extension.gen_crx(response)
    return response

def oxtail_xpi(request):
    extension = OxtailExtension(request.META['HTTP_HOST'], reverse('oxtail_index')[:-1])
    response = HttpResponse(mimetype='application/x-xpinstall')
    extension.gen_xpi(response)
    return response