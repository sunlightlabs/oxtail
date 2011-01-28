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
    
    if record.name and record.name not in [entity['name'] for entity in pg_data['entities'] if entity['tdata_id']]:
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
def process_pt(id):
    record = Record.objects.get(pk=id)
    pg_data = json.loads(record.pg_data)
    
    workers = []
    for entity in pg_data['entities']:
        if entity['tdata_type'] == 'politician':
            workers.append(process_pt_item.delay(entity['tdata_id']))
    
    results = dict([worker.get() for worker in workers])
    
    Record.objects.filter(pk=id).update(pt_data=json.dumps(results), pt_processed=True)

@task
def process_pt_item(tdata_id):
    info = api.entity_metadata(tdata_id)
    crp_ids = filter(lambda x: x['namespace'] == 'urn:crp:recipient', info['external_ids'])
    if crp_ids:
        crp_id = crp_ids[0]['id']
        pt_data = json.loads(urllib2.urlopen("http://politicalpartytime.org/json/%s/" % crp_id).read())
        if pt_data:
            upcoming = filter(lambda e: e['fields']['start_date'] >= "2010-01-26", pt_data)[:3]
            
            return (tdata_id, upcoming)
    return (tdata_id, [])

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
    process_pt.delay(id)
