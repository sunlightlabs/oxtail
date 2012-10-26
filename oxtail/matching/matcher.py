from collections import deque, defaultdict
from pytrie.pytrie import Trie
import csv
import re

# split on non-word sequences or non-space sequences with dots.
# this will make email addresses and URLs interspace. 
interspace_regex = re.compile("((?:\W+)|(?:\S+\.\S+))")


def tokenize(text):
    all_tokens = re.split("(\W+)", text)
    all_tokens = all_tokens[2 if all_tokens[0] == '' else 0 : len(all_tokens) - 2 if all_tokens[-1] == '' else len(all_tokens)]
    word_tokens = [all_tokens[i].lower() for i in xrange(0, len(all_tokens), 2)]
    return word_tokens


def token_match(trie, text, multiple=False):
    all_tokens = re.split(interspace_regex, text)
    all_tokens = all_tokens[2 if all_tokens[0] == '' else 0 : len(all_tokens) - 2 if all_tokens[-1] == '' else len(all_tokens)]
    word_tokens = [all_tokens[i].lower() for i in xrange(0, len(all_tokens), 2)]
    remaining_tokens = deque(word_tokens)
    result = defaultdict(set)
    
    while len(remaining_tokens) > 0:
        item = trie.longest_prefix_item(remaining_tokens, default=None)
        if item:
            match_start = len(all_tokens) - len(remaining_tokens) * 2 + 1
            match_end = match_start + len(item[0]) * 2 - 1
            (match, ids) = ("".join(all_tokens[match_start:match_end]), item[1])
            if multiple:
                for id in ids:
                    result[id].add(match)
            else:
                result[ids[0]].add(match)
            for _ in range(len(item[0])):
                remaining_tokens.popleft()
        else:
            remaining_tokens.popleft()
    
    return result


def build_token_trie(norm_iterable, blacklist={}):
    name_map = defaultdict(list)
    for name, id in norm_iterable:
        if name.lower().strip() not in blacklist:
            tokenized_name = tokenize(name)
            if not tokenized_name:
                raise Exception("Error: Trie input '%s' tokenized to empty string" % name)
            name_map[tuple(tokenized_name)].append(id)
    
    return Trie([(tokens, ids) for tokens, ids in name_map.iteritems()])

