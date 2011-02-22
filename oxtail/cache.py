from oxtail.tasks import generate_entity_data
from gevent.pool import Pool
import json
from influence.api import api
from oxtail.models import Entity
import urllib2
import csv
import itertools
from datetime import date

def build_cache(write, verbose=False):
    if verbose: print "Fetching entities..."
    
    entities = []
    for type in ['individual', 'organization', 'politician']:
        count = api.entity_count(type)
        for i in range(0, count, 10000):
            entities.extend(api.entity_list(i, i + 10000, type))
    
    def fetch(entity):
        if verbose: print 'Fetching record for %s %s (%s)...' % (entity['type'], entity['name'], entity['id'])
        try:
            record = generate_entity_data(entity['id'], skip_frequent=True)
            if not record:
                raise Exception()
            write(entity['id'], record['crp_id'] if record['crp_id'] else '', record)
        except:
            if verbose: print 'Warning: unable to fetch record for %s %s (%s).' % (entity['type'], entity['name'], entity['id'])
    
    if verbose: print 'Spawning fetch threads...'
    pool = Pool(6)
    
    for entity in entities:
        pool.spawn(fetch, entity)
    pool.join()
    if verbose: print 'Done.'

def update_pt_cache(get_entity_by_crp, write, verbose=False):
    if verbose: print "Fetching PT data..."
    csv_file = urllib2.urlopen("http://politicalpartytime.org/www/partytime_dump_all.csv")
    reader = csv.DictReader(csv_file)
    
    today = date.today().isoformat()
    if verbose: print "Filtering events..."
    events = [row for row in reader if row['Start_Date'] >= today]
    if verbose: print "Grouping and formatting events..."
    group_func = lambda e: e['CRP_ID'].strip()
    sorted_events = sorted(events, key=group_func)
    for crp_id, pol_events in itertools.groupby(sorted_events, group_func):
        sorted_events = sorted(pol_events, cmp=lambda a, b: cmp(a['Start_Date'], b['Start_Date']))[:3]
        formatted_events = [{
            "start_time": event['Start_Time'],
            "committee_id": event['Committee_Id'],
            "entertainment": event['Entertainment'],
            "contributions_info": event['Contributions_Info'],
            "venue": event['Venue_Name'],
            "partytime_id": event['key'],
            "start_date": event['Start_Date'],
            "beneficiaries": event['Beneficiary'].split(' || ') if event['Beneficiary'] else [],
            "hosts": event['Host'].split(' || ') if event['Host'] else [],
            "make_checks_payable_to": event['Make_Checks_Payable_To']
        } for event in sorted_events]
        entity = get_entity_by_crp(crp_id)
        if entity:
            entity_data = json.loads(entity)
            entity_data['upcoming_fundraisers'] = formatted_events
            write(entity_data['id'], crp_id, entity_data)
            if verbose: print "Wrote %s records for %s (%s)." % (len(formatted_events), entity_data['name'], entity_data['id'])

def write_postgres_record(id, crp_id, obj):
    e, created = Entity.objects.get_or_create(id=id)
    e.crp_id = crp_id
    e.json = json.dumps(obj)
    e.save()

def build_postgres_cache(verbose=False):    
    build_cache(write_postgres_record, verbose)

def update_postgres_pt_cache(verbose=False):
    update_pt_cache(get_postgres_entity_by_crp, write_postgres_record, verbose)

def get_postgres_entity(id):
    try:
        return Entity.objects.get(id=id).json
    except Entity.DoesNotExist:
        return None

def get_postgres_entity_by_crp(crp_id):
    if not crp_id:
        return None
    try:
        return Entity.objects.get(crp_id=crp_id).json
    except:
        return None