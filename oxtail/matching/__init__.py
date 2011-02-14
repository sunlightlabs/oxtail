basic_normalizer = str.lower

from oxtail.matching.matcher import build_token_trie, token_match
import os


_blacklist = set([
    'us', 
    'us government', 
    'va', 
    'madison',
    'alliance',
    'no one',
    'imagine',
    'impact',
])


_entity_trie = build_token_trie(open(os.path.join(os.path.dirname(__file__), 'normalized_aliases.csv'), 'r'), _blacklist)

def match(text):
    return token_match(_entity_trie, text)