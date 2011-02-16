from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from oxtail import tasks
from oxtail import cache

class CacheCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--backend',
            action='store',
            dest='backend',
            default=None
        ),
    )
    
    def handle(self, *args, **options):
        from gevent import monkey
        monkey.patch_all()
        
        if options['backend']:
            backend = options['backend']
        else:
            backend = getattr(settings, 'OXTAIL_CACHE', 'postgres')
        
        if backend not in ['postgres', 'redis']:
            raise CommandError('Backend must be postgres or redis.')
        
        getattr(cache, self.cache_function % backend, None)(verbose=True)