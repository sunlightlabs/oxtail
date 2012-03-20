from django.core.management.base import BaseCommand, CommandError
from oxtail.models import Entity
from oxtail.tasks import generate_entity_data
from oxtail.matching.normalize import normalize
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        for arg in args:
            entity_id = arg.replace('-', '')
            entity = Entity.objects.get(pk=entity_id)
            data = generate_entity_data(td_id=entity_id)
            aliases = normalize(data['raw_name'], data['type'])

            entity.json = json.dumps(data)
            entity.aliases = aliases

            print "Saving %s with aliases %s" % (entity.id, json.dumps(entity.aliases))

            entity.save()