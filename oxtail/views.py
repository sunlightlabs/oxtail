from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from urllib import urlencode
import os
import urllib2
import string
from django.conf import settings
from oxtail.decorators import cors_allow_all
from django.views.generic.simple import direct_to_template
from lookup import *
from oxtail.models import Record

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

def person_info(request):
    name = request.GET.get('name', '').strip()
    email = request.GET.get('email', '').strip()
    
    out = {}
    
    if email:
        out['email'] = email
        parts = email.split("@")
        if len(parts) > 1:
            domain = parts[1]
            out['domain'] = domain
            orgs = lookup_domain(domain)
            if orgs:
                out['organization'] = orgs[0]['name']
    
    if name:
        out['name'] = name
        if 'organization' in out:
            results = api._get_url_json('contributions.json', cycle=settings.LATEST_CYCLE, parse_json=True, contributor_ft=name, organization_ft=out['organization'])
            if results:
                out['indiv_contributions'] = results
        
        if 'indiv_contributions' not in out:
            results = api._get_url_json('contributions.json', cycle=settings.LATEST_CYCLE, parse_json=True, contributor_ft='John Thompson')
            out['indiv_contributions'] = results
    
    if 'organization' in out:
        org_results = api.entity_search(out['organization'])
        if org_results:
            out['org_info'] = org_results
    
    jout = json.dumps(out)
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], jout), 'text/javascript')
    else:
        return HttpResponse(jout, mimetype="application/json")

@cors_allow_all
def contextualize_text(request, pg_id=None):
    name = request.REQUEST.get('name', '').strip()
    email = request.REQUEST.get('email', '').strip()
    text = request.REQUEST.get('text', '').strip()
    
    ascii_text = filter(lambda x: x in string.printable, text)
    
    record = Record(name=name, email=email)
    record.set_hash(ascii_text)
    
    if email:
        record.email = email
        parts = email.split("@")
        if len(parts) > 1:
            domain = parts[1]
            orgs = lookup_domain(domain)
            if orgs:
                record.organization = orgs[0]['name']
    
    full_text = "%s<br />\n%s<br />\n%s" % (name, record.organization, ascii_text)
    
    if pg_id:
        data = urllib2.urlopen('http://poligraft.com/%s.json' % pg_id).read()
    else:
        data = urllib2.urlopen('http://poligraft.com/poligraft', urlencode({'json':1, 'text': full_text, 'suppresstext': 'true'})).read()
    jdata = json.loads(data)
    
    record.pg_data = data
    record.pg_id = jdata['slug']
    
    record.save()
    
    process_pg.apply_async(args=[record.id], countdown=2)
    
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], record.as_json()), 'text/javascript')
    else:
        return HttpResponse(record.as_json(), mimetype="application/json")

def contextualize_text_data(request, id):
    try:
        record = Record.objects.get(pg_id=id)
    except:
        return contextualize_text(request, id)
    
    if 'callback' in request.GET:
        return HttpResponse('%s(%s)' % (request.GET['callback'], record.as_json()), 'text/javascript')
    else:
        return HttpResponse(record.as_json(), mimetype="application/json")


# Browser extension code
from oxtail.extension import UserScriptExtension
class OxtailExtension(UserScriptExtension):
    id = 'oxtail@sunlightfoundation.com'
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

def oxtail_xpi(request):
    extension = OxtailExtension(request.META['HTTP_HOST'], getattr(settings, 'OXTAIL_PATH', '/gmail'))
    response = HttpResponse(mimetype='application/x-xpinstall')
    extension.gen_xpi(response)
    return response