from django.core.management.base import BaseCommand
from name_cleaver import PoliticianNameCleaver, RunningMatesNames
from optparse import make_option
import csv





def query_aliases(outfile):
    from django.db import connection
    
    c = connection.cursor()
    
    c.copy_expert("""
        COPY (select e.id, e.type, a.alias 
              from matchbox_entity e
              inner join matchbox_entityalias a
                  on a.entity_id = e.id)
        TO STDOUT CSV HEADER
    """, outfile)


def normalize_person(alias):
    parts = PoliticianNameCleaver(alias).parse()
    
    if isinstance(parts, RunningMatesNames):
        return normalize_person(str(parts.mate1)) + normalize_person(str(parts.mate2))
        
    permutations = [
        "%s %s" % (parts.first, parts.last),
        # caused too many false positives
#        "%s %s" % (parts.last, parts.first),
    ]
    if parts.middle:
        permutations.append("%s %s %s" % (parts.first, parts.middle, parts.last))
    
    return [s.lower() for s in permutations]



NORMALIZERS_BY_TYPE = {
   'individual': normalize_person,
   'organization': lambda x: [x],
   'politician': normalize_person,
   'industry': None,
}

def dump_normalizations(aliases_file, out_file):
    
    reader = csv.DictReader(aliases_file)
    writer = csv.writer(out_file)
    
    in_count = 0
    out_count = 0
    
    for line in reader:
        in_count += 1
        
        normalizer = NORMALIZERS_BY_TYPE[line['type']]
        if normalizer:
            for normalization in normalizer(line['alias']):
                writer.writerow([normalization, line['id']])
                out_count += 1

    print "Read %d aliases, wrote %s normalized strings." % (in_count, out_count)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-a", "--aliases", dest="alias_file", help="Dump of aliases from database.", default=None),
        make_option("-o", "--outfile", dest="normalized_file", help="Normalized output file.", default='normalized_aliases.csv'))
        
    def handle(self, *args, **options):
        alias_file = options['alias_file']
        
        if not alias_file:
            alias_file = 'aliases.csv'
            print "Querying aliases from database..."
            query_aliases(open(alias_file, 'w'))
            print "Done."
        
        aliases = open(alias_file, 'r')
        normalized = open(options['normalized_file'], 'w')
        
        dump_normalizations(aliases, normalized)
        
        
        
        
        
