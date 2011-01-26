from django.db import models
import hashlib
import json

class Record(models.Model):
    pg_data = models.TextField()
    pg_id = models.CharField(max_length=12)
    name = models.CharField(max_length=32, default='')
    email = models.CharField(max_length=64, default='')
    organization = models.CharField(max_length=64, default='')
    td_sender_info = models.TextField(default='')
    
    pg_processed = models.BooleanField(default=False)
    pt_processed = models.BooleanField(default=False)
    td_processed = models.BooleanField(default=False)
    
    text_hash = models.CharField(max_length=32, db_index=True)
    
    def set_hash(self, text):
        self.text_hash = hashlib.md5(self.name + self.email + text).hexdigest()
    
    def all_processed(self):
        return self.pg_processed and self.pt_processed and self.td_processed
    
    def as_json(self):
        j = json.loads(self.pg_data)
        j['pt_processed'] = self.pt_processed
        j['td_processed'] = self.td_processed
        j['all_processed'] = self.all_processed()
        j['sender_info'] = json.loads(self.td_sender_info) if self.td_sender_info else False
        
        return json.dumps(j)