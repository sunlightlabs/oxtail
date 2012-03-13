from django.db import models
from oxtail.fields import UUIDField, TruncatingCharField
from django.conf import settings
from arrayfields.fields import CharArrayField

class Entity(models.Model):
    id = UUIDField(primary_key=True, auto=False, db_index=True)
    crp_id = models.CharField(max_length=16, db_index=True, blank=True)
    aliases = CharArrayField(max_length=255, default='')
    json = models.TextField()

class Employer(models.Model):
    url = TruncatingCharField(max_length=255, db_index=True)
    resource_id = TruncatingCharField(max_length=255, db_index=True)
    name = TruncatingCharField(max_length=255, blank=True)