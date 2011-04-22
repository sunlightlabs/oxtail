from oxtail.models import Employer

def lookup_domain(domain):
    out = []
    orgs = Employer.objects.filter(url=domain)
    for org in orgs:
        out.append({'name': org.name, 'wikipedia_page': 'http://en.wikipedia.org/wiki/%s' % org.resource_id})
    
    return out
