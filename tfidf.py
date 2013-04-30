#  File: search.py
#  Project: Forking Stories
#  Component: Search engine
#
#  Authors:    Dominic May;
#              Lord_DeathMatch;
#              Mause
#
#  Description: uses the tf-idf algorithm to search the stories

# stdlib imports
import re
import os
import math
import json
import time
import logging
from collections import Counter


class Document(object):
    def __init__(self, raw, identifier, tokenizer):
        self.identifier = identifier

        self.tokens, self.num_tokens = tokenizer(raw)
        self.tokens = list(filter(lambda x: x not in self.stopwords, self.tokens))

        self.freq_map = Counter(self.tokens)
        self.freq_map_max = max(self.freq_map.values())

        self.tokens = set(self.tokens)


class TFIDF(object):
    def __init__(self):
        with open('stopwords.json') as fh:
            self.stopwords = set(json.load(fh))

        self.TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
        self.index = {}

    def tokenize(self, x):
        x = x.lower()
        x = self.TOKEN_RE.findall(x)
        return x, len(x)

    def term_freq(self, word, document, all_documents):
        maximum_occurances = document.freq_map_max
        # if not maximum_occurances:
        #     return document.freq_map[word]
        return document.freq_map[word] / float(maximum_occurances)

    def inverse_document_freq(self, word, all_documents, len_all_document):
        instances_in_all = len([1 for document in all_documents if word in document.tokens])
        # if not instances_in_all:
        #     return 1
        return math.log(len_all_document / instances_in_all)

    def build_index(self, directory, num=None):
        files = list(os.listdir(directory))
        files = files[:num] if num else files
        logging.info('Indexing {} items'.format(len(files)))

        start = time.time()
        logging.debug('Reading in and tokenising the documents started at {}'.format(start))

        # load in the documents
        all_documents = []
        for document in files:
            document = os.path.join(directory, document)
            identifier = document
            content = open(document).read()

            n_doc = self.Document(content, identifier=identifier)
            all_documents.append(n_doc)

        logging.debug('Ended after {} seconds'.format(time.time() - start))

        start = time.time()
        logging.debug('Computing the word relevancy values started at {}'.format(start))

        # compute the index
        i_d_v_cache = {}
        len_all_document = len(all_documents)
        for document in all_documents:
            self.index[document.identifier] = {}
            for word in document.tokens:
                if word not in i_d_v_cache:
                    i_d_v_cache[word] = self.inverse_document_freq(word, all_documents, len_all_document)

                value = self.term_freq(word, document, all_documents) * i_d_v_cache[word]

                self.index[document.identifier][word] = value

        logging.debug('Ended after {} seconds'.format(time.time() - start))
