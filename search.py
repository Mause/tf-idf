 #  File: search.py
 #  Project: Forking Stories
 #  Component: Search engine
 #
 #  Authors:    Dominic May;
 #              Lord_DeathMatch;
 #              Mause
 #
 #  Description: uses the tf-idf algorithm to search the stories

# stlid imports
import re
import os
import sys
import math
import json
import time
import logging
from itertools import chain
from collections import defaultdict, Counter

logging.info = print
logging.debug = print

with open('stopwords.json') as fh:
    stopwords = set(json.load(fh))


############ Index computation code ############
class Document(object):
    TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)

    def __init__(self, raw, identifier=None):
        self.identifier = identifier

        self.tokens, self.num_tokens = tokenize(raw, self.TOKEN_RE)
        self.tokens = list(filter(lambda x: x not in stopwords, self.tokens))

        self.freq_map = Counter(self.tokens)
        self.freq_map_max = max(self.freq_map.values())

        self.tokens = set(self.tokens)


def tokenize(x, TOKEN_RE):
    x = x.lower()
    x = TOKEN_RE.findall(x)
    return x, len(x)


def term_freq(word, document, all_documents):
    # maximum_occurances = max(document.freq_map.values())
    maximum_occurances = document.freq_map_max
    if not maximum_occurances:
        return document.freq_map[word]
    return document.freq_map[word] / float(maximum_occurances)


def inverse_document_freq(word, all_documents, len_all_document):
    instances_in_all = len([1 for document in all_documents if word in document.tokens])
    if not instances_in_all:
        return 1
    return math.log(len_all_document / instances_in_all)


def build_index(directory, num=None):
    files = list(os.listdir(directory))
    files = files[:num] if num else files
    logging.info('Indexing "{}" items'.format(len(files)))
    # read in the documents
    start = time.time()
    logging.debug('Reading in and tokenising the documents started at {}'.format(start))

    # load in the documents
    all_documents = []
    for document in files:
        document = os.path.join(directory, document)
        identifier = document
        content = open(document).read()

        n_doc = Document(content, identifier=identifier)
        all_documents.append(n_doc)

    logging.debug('Ended after {} seconds'.format(time.time() - start))

    start = time.time()
    logging.debug('Computing the word relevancy values started at {}'.format(start))

    # compute the index
    index = defaultdict(defaultdict)
    len_all_document = len(all_documents)
    for document in all_documents:
        for word in document.tokens:
            value = (
                term_freq(word, document, all_documents) *
                inverse_document_freq(word, all_documents, len_all_document))

            index[document.identifier][word] = value

    logging.debug('Ended after {} seconds'.format(time.time() - start))
    return index

############ Index storage code ############


def load_index():
    # read in the index, if it is cached
    with open('index.json') as fh:
        index = json.load(fh)

    return index


def save_index(index):
    with open('index.json', 'w') as fh:
        json.dump(index, fh, indent=4)


def search(index, query):

    logging.debug('Docs; {}'.format(len(index)))
    words = [x.lower() for x in query.split()]

    words = [word for word in words if word not in stopwords]

    logging.debug('Query with ; {}'.format(words))

    logging.debug('Unique indexed words; {}'.format(len(list(set(chain.from_iterable([x.keys() for x in index.values()]))))))
    scores = defaultdict(float)

    for page in index:
        for word in words:
            if word in index[page]:
                scores[page] += index[page][word]

    logging.debug('Relevant pages; {}'.format(len(scores)))
    scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return scores


def main():
    if len(sys.argv) > 1:
        index = build_index(sys.argv[1], num=150)
        save_index(index)
    else:
        index = load_index()

    # do the search function
    results = search(index, input('Q? '))
    print()

    for result in results:
        print(result[0], '-->', result[1])


if __name__ == '__main__':
    build_index(sys.argv[1], num=None)
    # main()
