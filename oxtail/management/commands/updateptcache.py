from oxtail.management.commands import CacheCommand

class Command(CacheCommand):
    cache_function = 'update_%s_pt_cache'