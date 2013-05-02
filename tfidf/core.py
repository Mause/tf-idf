# stdlib imports
import re
import math
import json
import time
import logging
from itertools import chain
from collections import Counter, defaultdict

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)

with open('stopwords.json') as fh:
    stopwords = set(json.load(fh))


class Document(object):
    def __init__(self, content, identifier, metadata):
        self.identifier = identifier

        self.tokens, self.num_tokens = self.tokenize(content)
        self.tokens = list(filter(lambda x: x not in stopwords, self.tokens))

        self.freq_map = Counter(self.tokens)
        self.freq_map_max = max(self.freq_map.values())

        self.tokens = set(self.tokens)

    def tokenize(self, x):
        x = x.lower()
        x = TOKEN_RE.findall(x)
        return x, len(x)


class TFIDF(object):
    # this kind of has to be here
    index_loaded = False
    index = {}
    index_metadata = {}

    # if either of the next two functions ever error out, use the "better to break something and apologise" methodology
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

    def build_index(self, num=None):
        start = time.time()
        logging.debug('Reading in and tokenising the documents started at {}'.format(start))

        # load in the documents
        all_documents = []
        for data in self.documents(num):
            data
            n_doc = Document(
                content=data["content"],
                identifier=data["identifier"],
                metadata={})
            all_documents.append(n_doc)

        logging.debug('Ended after {} seconds'.format(time.time() - start))

        start = time.time()
        logging.debug('Computing the word relevancy values started at {}'.format(start))

        # compute the index
        i_d_v_cache = {}
        len_all_document = len(all_documents)
        for document in all_documents:
            self.index[document.identifier] = {
                "metadata": {},
                "words": {}
            }

            for word in document.tokens:
                if word not in i_d_v_cache:
                    i_d_v_cache[word] = self.inverse_document_freq(word, all_documents, len_all_document)

                self.index[document.identifier]["words"][word] = (
                    self.term_freq(word, document, all_documents) * i_d_v_cache[word]
                )

        logging.debug('Ended after {} seconds'.format(time.time() - start))
        self.index_loaded = True

    def search(self, query):
        if not self.index_loaded:
            self.build_index()

        logging.debug('Docs; {}'.format(len(self.index)))

        words = [x.lower() for x in query.split()]

        words = [
            word
            for word in words
            if word not in stopwords]

        # this implementation does not place emphasis on words
        # that appear more than once in the query string
        words = set(words)

        logging.debug('Querying with; {}'.format(words))

        # <3 default dict
        scores = defaultdict(lambda: {"score": 0})
        for page in self.index:
            for word in words:
                if word in self.index[page]["words"]:
                    scores[page]["score"] += self.index[page]["words"][word]

        logging.debug('Relevant documents; {}'.format(len(scores)))
        scores = sorted(
            scores.items(), key=lambda x: x[1]["score"], reverse=True)

        return scores

    def mould_metadata(self):
        all_words = chain.from_iterable(
            [x['words'].keys() for x in self.index.values()])
        all_words = set(all_words)
        self.index_metadata.update({
            'uniq_words': len(all_words)
        })
        return self.index_metadata

    def load_index(self):
        raise NotImplementedError()

    def save_index(self):
        raise NotImplementedError()

    def documents(self):
        # must return dictionary, in format;
        # {
        #     "identifier": str,
        #     "content": str,
        #     "metadata": dict
        # }
        raise NotImplementedError()
