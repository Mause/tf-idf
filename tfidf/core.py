"core functionality"

# stdlib imports
import os
import math
import json
import time
import logging
from collections import (
    Counter,
    defaultdict,
    OrderedDict
)
from itertools import chain

from .utils import tokenize
from .mixins import MixinSettings

with open(os.path.join(os.path.dirname(__file__), 'stopwords.json')) as fh:
    stopwords = set(json.load(fh))


class Document(object):
    "a container object for properties of a given document"
    def __init__(self, content, identifier, metadata):
        self.metadata = metadata
        self.identifier = identifier

        self.tokens, self.num_tokens = tokenize(content)
        self.raw_tokens = list(filter(lambda x: x not in stopwords, self.tokens))

        self.freq_map = Counter(self.raw_tokens)
        self.freq_map_max = max(self.freq_map.values())

        self.tokens = set(self.raw_tokens)

    def __repr__(self):
        return '<Document identifier="{}" metadata="{}" tokens="{}">'.format(
            self.identifier,
            self.metadata,
            self.tokens)


class TFIDF(MixinSettings):
    "An implementation of TFIDF"

    # these can't be assigned in a __init__ method, cause it would overwrite the one MixinSettings
    index_loaded = False
    index = defaultdict(dict)
    index_metadata = {}

    @property
    def enforce_correct(self):
        """
        some modifications can be made in the algorithm to make it more reliable,
        these are disabled by default

        enable them by passing enforce_correct=True to the constructor
        """
        return 'enforce_correct' in self.settings and self.settings['enforce_corrent']

    def term_freq(self, word, document, all_documents):
        "calculates the term frequency for a word"
        # the word with the most occurrences in the document does not depend on the current word;
        # so, we store it as a constant on the Document :D
        maximum_occurances = document.freq_map_max

        if self.enforce_correct:
            maximum_occurances += 0.5

        return document.freq_map[word] / float(maximum_occurances)

    def inverse_document_freq(self, word, all_documents, len_all_document, idf_ref):
        "calculates idf for given word with given document stats"
        instances_in_all = idf_ref[word]

        # as stated on Wikipedia, if the document does not exist in any documents,
        # instances_in_all will be zero, causing a ZeroDivisionError.
        # 1 is hence added to ensure this does not occur
        if self.enforce_correct:
            instances_in_all += 1

        return math.log(len_all_document / float(instances_in_all))

    def process_documents(self, num=None):
        """
        calls the self.documents() function, and iterates over it,
        returning a list of Document instances
        """
        start = time.time()
        logging.debug('Reading and tokenizing the documents started at {}'.format(start))

        # load in the documents
        all_documents = []
        for data in self.documents(num):
            n_doc = Document(
                content=data["content"],
                identifier=data["identifier"],
                metadata=data['metadata'] if 'metadata' in data else {})

            all_documents.append(n_doc)

        logging.debug('Ended after {} seconds'.format(time.time() - start))

        return all_documents

    def build_idf_reference(self, all_documents: Document):
        """
        returns a collections.Counter() instance
        recording how many documents contain a given term
        """
        tokens = chain.from_iterable(document.tokens for document in all_documents)
        return Counter(tokens)

    def build_index(self, num=None):
        """
        computes tfidf for document and terms.
        assigns the resulting index to self.index
        """
        all_documents = self.process_documents(num)
        len_all_document = len(all_documents)

        logging.debug('Building reference table')
        idf_ref = self.build_idf_reference(all_documents)

        start = time.time()
        logging.debug('Computing the word relevancy values started at {}'.format(start))

        # compute the index
        i_d_f_cache = {}
        for document in all_documents:
            for word in document.tokens:
                if word not in i_d_f_cache:
                    i_d_f_cache[word] = self.inverse_document_freq(
                        word, all_documents,
                        len_all_document, idf_ref)

                self.index[word][document.identifier] = (
                    self.term_freq(word, document, all_documents) * i_d_f_cache[word]
                )

        logging.debug('Ended after {} seconds'.format(time.time() - start))
        self.index_loaded = True

    def normalise_search_results(self, words: list, results: dict):
        """
        aims to promote results that contain more of the specified keywords

        whether or not it achieves this is debatable, but comments are welcome
        """
        for result in results:
            if results[result]['words_contained'] != words:
                diff = words - results[result]['words_contained']
                diff = len(diff) / len(words)

                results[result]['original'] = results[result]['score']
                results[result]['score'] *= diff
                results[result]['diff'] = diff
            else:
                results[result]['diff'] = 1.0
                results[result]['original'] = results[result]['score']
        return results

    def word_scores_from_index(self):
        """
        sums all the scores for a particular word,
        and assigns it to a dictionary, with the word as the key
        """
        # <3 dictionary comprehension
        return {word: sum(self.index[word].values()) for word in self.index}

    def search(self, query: str):
        """
        uses the index to find documents relating to the query

        returns a collections.OrderedDict() sorted by score
        """
        if not self.index_loaded:
            self.build_index()

        logging.debug('Docs; {}'.format(len(self.index)))

        words = [x.lower() for x in query.split()]

        words = self.filter_out_stopwords(words)

        # this implementation does not place emphasis on words
        # that appear more than once in the query string
        words = set(words)

        logging.debug('Querying with; {}'.format(words))

        # <3 default dict
        scores = defaultdict(lambda: {"score": 0, "words_contained": set()})
        words_not_found = set()
        for word in words:
            if word in self.index:
                for document in self.index[word]:
                    scores[document]["score"] += self.index[word][document]
                    scores[document]["words_contained"].add(word)
            else:
                words_not_found.add(word)

        scores = self.normalise_search_results(words, scores)

        if words_not_found:
            logging.warning(' words not in index; {}'.format(words_not_found))
        logging.debug('Relevant documents; {}'.format(len(scores)))

        scores = sorted(
            scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True)
        scores = OrderedDict(scores)

        return scores

    def mould_metadata(self):
        "atm, simple grabs the number of words in the index"
        all_words = self.index.keys()
        all_words = set(all_words)
        self.index_metadata['uniq_words'] = len(all_words)
        return self.index_metadata

    def filter_out_stopwords(self, words: list):
        "returns a filter instance configured to generate words, minus the stopwords"
        return filter(lambda word: word not in stopwords, words)

    def determine_keywords(self, string: str):
        """
        lower scores are sorta better; less common in the index, hence presumed to be more informative
        """

        tokens = tokenize(string)
        word_scores = self.word_scores_from_index()

        scores = {
            word: word_scores[word] if word in word_scores else 0
            for word in tokens
        }

        scores = sorted(scores.items(), key=lambda x: x[1])
        scores = OrderedDict(scores)

        return scores

    def __repr__(self):
        return '<{} {}>'.format(
            self.__class__.__name__,
            self.settings)

    def load_index(self):
        """
        must not return anything, must simply loads index into self.index

        must be implemented by subclass
        """
        raise NotImplementedError('Must be implemented in subclass')

    def save_index(self):
        """
        does not require arguments, simple saves index from self.index

        must be implemented by subclass
        """
        raise NotImplementedError('Must be implemented in subclass')

    def documents(self):
        """
        must return an iterable yielding dictionaries as follows;
        {
            "identifier": str,
            "content": str,
            "metadata": dict
        }

        must be implemented by subclass
        """
        raise NotImplementedError('Must be implemented in subclass')
