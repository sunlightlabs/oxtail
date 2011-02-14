from oxtail.matching import basic_normalizer
from pytrie.pytrie import Trie
import re
import csv


def token_match(trie, text):
    text = re.split("\W+", basic_normalizer(text))
    result = list()
    
    i = 0
    while i < len(text):
        item = trie.longest_prefix_item(text[i:], default=None)
        if item:
            (match, id) = (" ".join(item[0]), item[1])
            result.append((match, id))
            i += len(item[0])
        else:
            i += 1
    
    return result


def build_token_trie(norm_file, blacklist={}):
    return Trie([(l[0].split(), l[1]) for l in csv.reader(norm_file) if l[0] not in blacklist])

