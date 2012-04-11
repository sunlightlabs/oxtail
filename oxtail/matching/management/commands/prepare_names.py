from django.core.management.base import BaseCommand
from name_cleaver import PoliticianNameCleaver, IndividualNameCleaver, RunningMatesNames, UnparseableNameException
from optparse import make_option
import csv


def query_aliases(outfile):
    from django.db import connections
    
    c = connections['td'].cursor()
    
    c.copy_expert("""
        COPY (select e.id, e.type, a.alias 
              from matchbox_entity e
              inner join matchbox_entityalias a
                  on a.entity_id = e.id)
        TO STDOUT CSV HEADER
    """, outfile)


def normalize_politician(alias):
    parts = PoliticianNameCleaver(alias).parse()

    if isinstance(parts, RunningMatesNames):
        return get_name_permutations(parts.mate1) + get_name_permutations(parts.mate2)

    return [s.lower() for s in get_name_permutations(parts)]


def get_name_permutations(name):

    options = [ name.primary_name_parts() ]

    if name.middle:
        options.append(name.primary_name_parts(include_middle=True))

    return [ ' '.join(x) for x in options ]


NORMALIZERS_BY_TYPE = {
   'individual': lambda x: get_name_permutations(IndividualNameCleaver(x).parse()),
   'organization': lambda x: [x],
   'politician': normalize_politician,
   'industry': None,
}

def dump_normalizations(aliases_file, out_file):

    reader = csv.DictReader(aliases_file)
    writer = csv.writer(out_file)

    in_count = 0
    out_count = 0

    for line in reader:
        in_count += 1

        try:
            normalizer = NORMALIZERS_BY_TYPE[line['type']]
            for normalization in normalizer(line['alias']):
                writer.writerow([normalization, line['id']])
                out_count += 1
        except UnparseableNameException, e:
            print "Error parsing '%s'. Skipping alias." % line['alias']
        except TypeError:
            print "Industry found. Skipping alias '%s'." % line['alias']
        except KeyError:
            print "Error: Known entity type not found in line: '%s'." % '|'.join(line)

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
        
        
        
        
        
