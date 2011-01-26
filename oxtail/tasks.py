from celery.task import task
import json
import urllib2
from oxtail.models import Record
from influence.api import api
from django.conf import settings

@task
def process_td(id):
    record = Record.objects.get(pk=id)
    pg_data = json.loads(record.pg_data)
    
    if record.name and record.name not in [entity['name'] for entity in pg_data['entities']]:
        if record.organization:
            results = api._get_url_json('contributions.json', cycle=settings.LATEST_CYCLE, parse_json=False, contributor_ft=record.name, organization_ft=record.organization)
            if results:
                record.td_sender_info = results
        
        if not record.td_sender_info:
            results = api._get_url_json('contributions.json', cycle=settings.LATEST_CYCLE, parse_json=False, contributor_ft=record.name)
            record.td_sender_info = results
    
    record.td_processed = True
    
    # do an update rather than a save, to avoid race conditions
    Record.objects.filter(pk=id).update(td_sender_info=record.td_sender_info, td_processed=record.td_processed)

@task
def process_pg(id):
    record = Record.objects.get(pk=id)
    
    data = urllib2.urlopen('http://poligraft.com/%s.json' % record.pg_id).read()
    jdata = json.loads(data)
    
    if jdata['processed'] == True:
        Record.objects.filter(pk=id).update(pg_data=data, pg_processed=True)
        post_pg(id)
    else:
        process_pg.apply_async(args=[id], countdown=2)

def post_pg(id):
    process_td.delay(id)
