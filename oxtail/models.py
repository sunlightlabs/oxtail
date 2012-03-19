from django.db import models
from oxtail.fields import UUIDField, TruncatingCharField
from django.conf import settings
from arrayfields.fields import CharArrayField
import itertools

class Entity(models.Model):
    id = UUIDField(primary_key=True, auto=False, db_index=True)
    crp_id = models.CharField(max_length=16, db_index=True, blank=True)
    aliases = CharArrayField(max_length=255, default='')
    json = models.TextField()

    @classmethod
    def all_aliases(cls):
        return itertools.chain.from_iterable(
            itertools.imap(
                lambda entity: [(alias, entity.id) for alias in entity.aliases],
                cls.objects.all().order_by('id')
            )
        )

class Employer(models.Model):
    url = TruncatingCharField(max_length=255, db_index=True)
    resource_id = TruncatingCharField(max_length=255, db_index=True)
    name = TruncatingCharField(max_length=255, blank=True)