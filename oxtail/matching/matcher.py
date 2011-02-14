from oxtail.matching import basic_normalizer
from pytrie.pytrie import Trie
import re
import time
import csv



def token_match(trie, text):
    start = time.clock()
    
    text = re.split("\W+", basic_normalizer(text))
    
    i = 0
    while i < len(text):
        item = trie.longest_prefix_item(text[i:], default=None)
        
        if item:
            (match, id) = (" ".join(item[0]), item[1])
            print "Matched '%s' as %s" % (match, id)
            i += len(item[0])
        else:
            i += 1
    
    print "%f seconds elapsed." % (time.clock() - start)    


def build_token_trie(norm_file):
    return Trie([(l[0].split(), l[1]) for l in csv.reader(norm_file)])

