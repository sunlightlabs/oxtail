from django.db import models
from oxtail.uuid_field import UUIDField
from django.conf import settings

class Entity(models.Model):
    id = UUIDField(primary_key=True, auto=False, db_index=True)
    crp_id = models.CharField(max_length=16, db_index=True, blank=True)
    json = models.TextField()