from oxtail.matching import basic_normalizer
from pytrie.pytrie import Trie
import re
import csv
from collections import deque, defaultdict


def token_match(trie, text):
    split_text = re.split("(\W+)", text)
    remaining_tokens = deque([basic_normalizer(split_text[i]) for i in xrange(0, len(split_text), 2)])
    result = defaultdict(set)
    
    while len(remaining_tokens) > 0:
        item = trie.longest_prefix_item(remaining_tokens, default=None)
        if item:
            match_start = len(split_text) - len(remaining_tokens) * 2 + 1
            match_end = match_start + len(item[0]) * 2 - 1
            (match, id) = ("".join(split_text[match_start:match_end]), item[1])
            result[id].add(match)
            for _ in range(len(item[0])):
                remaining_tokens.popleft()
        else:
            remaining_tokens.popleft()
    
    return result


def build_token_trie(norm_file, blacklist={}):
    return Trie([(l[0].split(), l[1]) for l in csv.reader(norm_file) if l[0] not in blacklist])

