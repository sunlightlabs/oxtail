
from oxtail.matching.matcher import build_token_trie, token_match
import os
import csv

try:
    from django.conf import settings
    DEBUG = settings.DEBUG
except ImportError:
    DEBUG = False


_blacklist = set([
    'us', 
    'us government', 
    'va', 
    'madison',
    'alliance',
    'no one',
    'imagine',
    'impact',
    'leadership pac',
    'advocacy group',
    'public campaign',
    'network',
    'for pac',
    'the nation',
    'a white',
    'member',
    'project management',
    'white house',
    'a cloud',
    'tuesday morning',
    'a pac',
    'office buildings',
    'lobbying firm',
    'nationwide',
    'public service',
    'public private partnership'
])

def load_trie_from_csv():
    data_dir = os.path.dirname(__file__)
    global _entity_trie
    _entity_trie = build_token_trie(
        csv.reader(
            open(os.path.join(data_dir, 'normalized_aliases.csv'), 'r'),

        ),
        _blacklist
    )

def load_trie_from_db():
    from oxtail.models import Entity

    global _entity_trie
    _entity_trie = build_token_trie(
        Entity.all_aliases(),
        _blacklist
    )

def match(text, multiple=False):
    return token_match(_entity_trie, text, multiple)

