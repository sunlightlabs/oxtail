import csv

from django.core.management.base import BaseCommand

from oxtail.matching import match


class Command(BaseCommand):
    """
    Compute text matches on a CSV file.
    
    Input file should have two columns: an ID and a free text column. The ID is uninterpretted and can be anything.
    The text is matched against entity aliases as check in on Oxtail. Matches are written to a two column output
    file. Columns are the ID from the input file and the entity ID of the match. May be multiple entities per input ID.
    """
    
    def handle(self, *args, **options):
        reader = csv.reader(open(args[0], 'r'))
        writer = csv.writer(open(args[1], 'w'))
        
        for (id, text) in reader:
            for entity_id in match(text, multiple=True).keys():
                writer.writerow([id, entity_id])