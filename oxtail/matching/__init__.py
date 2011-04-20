basic_normalizer = str.lower

from oxtail.matching.matcher import build_token_trie, token_match
import os
import cPickle


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
])


data_dir = os.path.dirname(__file__)
trie_file = os.path.join(data_dir, 'normalized_aliases.trie')
if os.path.exists(trie_file):
    trie_handle = open(trie_file, 'r')
    _entity_trie = cPickle.load(trie_handle)
    trie_handle.close()
else:
    _entity_trie = build_token_trie(open(os.path.join(data_dir, 'normalized_aliases.csv'), 'r'), _blacklist)
    trie_handle = open(trie_file, 'w')
    cPickle.dump(_entity_trie, trie_handle, cPickle.HIGHEST_PROTOCOL)
    trie_handle.close()

def match(text):
    return token_match(_entity_trie, text)
