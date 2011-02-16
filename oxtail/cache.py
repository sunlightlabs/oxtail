from oxtail.tasks import generate_entity_data
from gevent.pool import Pool
import json
from influence.api import api
from oxtail.models import Entity

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

def write_postgres_record(id, crp_id, obj):
    e, created = Entity.objects.get_or_create(id=id)
    e.crp_id = crp_id
    e.json = json.dumps(obj)
    e.save()

def build_postgres_cache(verbose=False):    
    build_cache(write_postgres_record, verbose)

def get_postgres_entity(id):
    try:
        return Entity.objects.get(id=id).json
    except Entity.DoesNotExist:
        return None