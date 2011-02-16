from oxtail.management.commands import CacheCommand

class Command(CacheCommand):
    cache_function = 'build_%s_cache'