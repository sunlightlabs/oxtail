import json
import urllib2
from influence.api import api
from influence.names import standardize_name
from django.conf import settings
from django.template.defaultfilters import slugify
from datetime import date
from name_cleaver import PoliticianNameCleaver
from oxtail.util import is_int, seat_labels, cache as cache_decorate

def generate_entity_data(td_id, skip_frequent=False):
    td_metadata = api.entity_metadata(td_id)
    if not bool(td_metadata['totals']):
        return None
    
    struct = {
        'id': td_metadata['id'],
        'name': str(standardize_name(td_metadata['name'], td_metadata['type'])),
        'raw_name': td_metadata['name'],
        'type': td_metadata['type'],
        'bioguide_id': td_metadata['metadata'].get('bioguide_id', None),
        'seat': None,
        'seat_label': None,
        'held_seat': None,
        'affiliated_organizations': None
    }
    struct['slug'] = slugify(struct['name'])
    if struct['type'] == 'politician':
        # politician name
        poli_name = PoliticianNameCleaver(td_metadata['name']).parse().plus_metadata(td_metadata['metadata']['party'], td_metadata['metadata']['state'])
        struct['name'] = str(poli_name)
        
        # politician office info
        years = sorted([key for key in td_metadata['metadata'].keys() if is_int(key)])
        
        wins = [td_metadata['metadata'][year] for year in years if td_metadata['metadata'][year]['seat_result'] == 'W']
        if wins:
            struct['seat'] = wins[-1]['seat']
            struct['held_seat'] = True
        else:
            losses = [td_metadata['metadata'][year] for year in years if td_metadata['metadata'][year]['seat_result'] == 'L']
            if losses:
                struct['seat'] = losses[-1]['seat']
                struct['held_seat'] = False
            elif years:
                struct['seat'] = td_metadata['metadata'][years[-1]]['seat']
                struct['held_seat'] = False
        
        if struct['seat'] and struct['seat'] in seat_labels:
            struct['seat_label'] = seat_labels[struct['seat']]
        
    elif struct['type'] == 'individual':
        if 'affiliated_organizations' in td_metadata['metadata'] and type(td_metadata['metadata']['affiliated_organizations']) == list and len(td_metadata['metadata']['affiliated_organizations']) > 0:
            struct['affiliated_organizations'] = [{
                'type': org['type'],
                'name': org['name'],
                'id': org['id'],
                'slug': slugify(standardize_name(org['name'], org['type']))
            } for org in td_metadata['metadata']['affiliated_organizations']]
    
    crp_ids = filter(lambda x: x['namespace'] == 'urn:crp:recipient', td_metadata['external_ids'])
    if crp_ids:
        struct['crp_id'] = crp_ids[0]['id']
    else:
        struct['crp_id'] = None
    
    struct['campaign_finance'] = fetch_finance(td_metadata)
    
    struct['lobbying'] = fetch_lobbying(td_metadata)
    
    struct['upcoming_fundraisers'] = fetch_pt(td_metadata) if not skip_frequent else None
    
    return struct

# rearranging imports to avoid circular import
from oxtail import cache

def get_entity_data(tdata_id):
    cache_backend = getattr(settings, 'OXTAIL_CACHE', False)
    if cache_backend:
        entity = getattr(cache, 'get_%s_entity' % cache_backend)(tdata_id)
        if entity:
            return json.loads(entity)
        else:
            return None
    else:
        return generate_entity_data(tdata_id)

def fetch_finance(td_metadata):
    td_id = td_metadata['id']
    type = td_metadata['type']
    out = {}
    if type == 'organization' or type == 'industry':
        recipient_breakdown = api.org_party_breakdown(td_id)
        out['recipient_breakdown'] = {'dem': float(recipient_breakdown.get('Democrats', [0, 0])[1]), 'rep': float(recipient_breakdown.get('Republicans', [0, 0])[1]), 'other': float(recipient_breakdown.get('Other', [0, 0])[1])}
        out['contributor_type_breakdown'] = None
        out['contributor_local_breakdown'] = None
        out['top_industries'] = None
        
        # for totals in TD, the 'contributor' and 'recipient' totals seem backwards, so I'm just going to call everything 'contribution' here
        out['contribution_total'] = td_metadata['totals']['-1']['contributor_amount']
    
    elif type == 'individual':
        recipient_breakdown = api.indiv_party_breakdown(td_id)
        out['recipient_breakdown'] = {'dem': float(recipient_breakdown.get('Democrats', [0, 0])[1]), 'rep': float(recipient_breakdown.get('Republicans', [0, 0])[1]), 'other': float(recipient_breakdown.get('Other', [0, 0])[1])}
        out['contributor_type_breakdown'] = None
        out['contributor_local_breakdown'] = None
        out['top_industries'] = None
        
        out['contribution_total'] = td_metadata['totals']['-1']['contributor_amount']
    
    elif type == 'politician':
        out['recipient_breakdown'] = None
        contributor_type_breakdown = api.pol_contributor_type_breakdown(td_id)
        out['contributor_type_breakdown'] = {'individual': float(contributor_type_breakdown.get('Individuals', [0, 0])[1]), 'pac': float(contributor_type_breakdown.get('PACs', [0, 0])[1])}
        contributor_local_breakdown = api.pol_local_breakdown(td_id)
        out['contributor_local_breakdown'] = {'in_state': float(contributor_local_breakdown.get('in-state', [0, 0])[1]), 'out_of_state': float(contributor_local_breakdown.get('out-of-state', [0, 0])[1])}
        
        top_industries = api.pol_industries(td_id)
        out['top_industries'] = [{
            'amount': float(s['amount']),
            'id': s['id'],
            'name': standardize_name(s['name'], 'industry'),
            'slug': slugify(standardize_name(s['name'], 'industry')),
            'type': 'industry',
        } for s in top_industries if s['should_show_entity']][:5]
        
        out['contribution_total'] = td_metadata['totals']['-1']['recipient_amount']
    
    return out

def fetch_lobbying(td_metadata):
    td_id = td_metadata['id']
    type = td_metadata['type']
    out = {}
    
    if type == 'organization' or type == 'industry':
        out['top_issues'] = api.org_issues(td_id)[:5]
        out['expenditures'] = float(td_metadata['totals']['-1']['non_firm_spending']) + float(td_metadata['totals']['-1']['firm_income'])
        out['is_lobbyist'] = False
        if td_metadata['metadata']['lobbying_firm']:
            out['top_issues'] = api.org_registrant_issues(td_id)[:5]
            out['is_lobbying_firm'] = True
            out['clients'] = [{
                'name': standardize_name(client['client_name'], 'organization'),
                'slug': slugify(standardize_name(client['client_name'], 'organization')),
                'count': client['count'],
                'id': client['client_entity'],
                'type': 'organization',
            } for client in api.org_registrant_clients(td_id)][:5]
        else:
            out['top_issues'] = api.org_issues(td_id)[:5]
            out['is_lobbying_firm'] = False
            out['clients'] = None
    
    elif type == 'individual':
        out['is_lobbyist'] = bool(td_metadata['lobbying_years'])
        out['is_lobbying_firm'] = None
        if out['is_lobbyist']:
            out['top_issues'] = api.org_issues(td_id)[:5]
            out['clients'] = [{
                'name': standardize_name(client['client_name'], 'organization'),
                'slug': slugify(standardize_name(client['client_name'], 'organization')),
                'count': client['count'],
                'id': client['client_entity'],
                'type': 'organization',
            } for client in api.indiv_clients(td_id)][:5]
        else:
            out['top_issues'] = None
            out['clients'] = None
    
    elif type == 'politician':
        out['is_lobbyist'] = None
        out['is_lobbying_firm'] = None
        out['top_issues'] = None
        out['expenditures'] = None
        out['is_lobbying_firm'] = None
    
    return out

def fetch_pt(td_metadata):
    if td_metadata['type'] == 'politician':
        out = []
        crp_ids = filter(lambda x: x['namespace'] == 'urn:crp:recipient', td_metadata['external_ids'])
        if crp_ids:
            crp_id = crp_ids[0]['id']
            pt_data = json.loads(urllib2.urlopen("http://politicalpartytime.org/json/%s/" % crp_id).read())
            if pt_data:
                upcoming = filter(lambda e: e['fields']['start_date'] >= date.today().isoformat(), pt_data)[:3]
                
                for event in upcoming:
                   entry = event['fields'].copy()
                   entry['partytime_id'] = event['pk']
                   out.append(entry)
        return out
    else:
        return None
    
@cache_decorate(seconds=86400)
def ip_lookup(ip):
    try:
        loc_data = json.loads(urllib2.urlopen("http://api.ipinfodb.com/v3/ip-city/?key=%s&ip=%s&format=json" % (settings.GEO_API_KEY, ip), timeout=1).read())
        lat = float(loc_data['latitude'])
        lon = float(loc_data['longitude'])
        return (lat, lon)
    except:
        return None

def process_td(id):
    record = Record.objects.get(pk=id)
    pg_data = json.loads(record.pg_data)
    
    if record.name and record.name not in [entity['name'] for entity in pg_data['entities'] if entity['tdata_id']]:
        if record.organization:
            results = api._get_url_json('contributions.json', parse_json=False, contributor_ft=record.name, organization_ft=record.organization)
            if json.loads(results):
                record.td_sender_info = results
        
        if not record.td_sender_info:
            results = api._get_url_json('contributions.json', parse_json=False, contributor_ft=record.name)
            record.td_sender_info = results
    
    record.td_processed = True
    
    # do an update rather than a save, to avoid race conditions
    Record.objects.filter(pk=id).update(td_sender_info=record.td_sender_info, td_processed=record.td_processed)

def process_pt(id):
    record = Record.objects.get(pk=id)
    pg_data = json.loads(record.pg_data)
    
    workers = []
    for entity in pg_data['entities']:
        if entity['tdata_type'] == 'politician':
            workers.append(process_pt_item.delay(entity['tdata_id']))
    
    results = dict([worker.get() for worker in workers])
    
    Record.objects.filter(pk=id).update(pt_data=json.dumps(results), pt_processed=True)

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
