from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from oxtail.models import Employer
import filelike
import json
import re
import sys

def dbpedia_tokenize(line):
    line = line.strip()
    tokens = line.split(" ", 2)
    
    subj = tokens[0][29:-1]
    verb = tokens[1][1:-1]
    
    obj = tokens[2]
    
    if obj.endswith(" ."):
        obj = obj[:-2]
    
    if obj.endswith("@en"):
        obj = obj[:-3]
    
    obj = json.loads('"%s"' % obj[1:-1])
    
    return (subj, verb, obj)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--titles-only',
            action='store_true',
            dest='titles_only',
            default=False
        ),
        make_option('--titles-file',
            action='store',
            dest='titles_file',
            default=None
        ),
    )
    
    def handle(self, *args, **options):
        
        if not options['titles_only']:
            # delete stale data
            print "Clearing database..."
            Employer.objects.all().delete()
            
            # first build the initial dataset from the domain name record
            print "Building homepage list..."
            page_re = re.compile(r"^(https?://)?(www\.)?(?P<domain>[\w\.]+)/?$")
            homepages = filelike.open("http://downloads.dbpedia.org/3.7/en/homepages_en.nt.bz2")
            hp_count = 0
            for line in homepages:
                subj, verb, obj = dbpedia_tokenize(line)
                match = page_re.match(obj)
                if match:
                    md = match.groupdict()
                    emp = Employer(url=md['domain'], resource_id=subj)
                    emp.save()
                    hp_count += 1
                    if hp_count % 10000 == 0:
                        print "Added %s records" % hp_count
            homepages.close()
        
        print "Matching names to domains..."
        titles_file = options['titles_file'] if options['titles_file'] else "http://downloads.dbpedia.org/3.7/en/labels_en.nt.bz2"
        print "Using %s" % titles_file
        titles = filelike.open(titles_file)
        t_count = 0
        for line in titles:
            try:
                subj, verb, obj = dbpedia_tokenize(line)
            except:
                continue
            try:
                emp = Employer.objects.get(resource_id=subj)
                emp.name = obj
                emp.save()
                t_count += 1
                if t_count % 10000 == 0:
                    print "Updated %s records" % t_count
            except Employer.DoesNotExist:
                pass
        titles.close()