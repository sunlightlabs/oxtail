# use TD's metadata for API keys

class LocksmithRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.db_table == 'locksmith_auth_apikey':
            return 'td_meta'
        return None
    
    def allow_syncdb(self, db, model):
        if model._meta.db_table == 'locksmith_auth_apikey':
            return False
        return None
