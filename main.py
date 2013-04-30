import os
import json
import logging
from itertools import chain
from collections import defaultdict

from tfidf import TFIDF


logging.info = print
logging.debug = print
logging.warning = print


class TFIDF_JSON(TFIDF):
    def __init__(self, filename):
        self.filename = filename
        self.index = None
        self.load_index()
        return super(TFIDF_JSON, self).__init__()

    def load_index(self):
        if not os.path.exists(self.filename):
            return {}
        # read in the index, if it is cached
        with open(self.filename) as fh:
            self.index = json.load(fh)

    def save_index(self):
        with open(self.filename, 'w') as fh:
            json.dump(self.index, fh, indent=4)

    def search(self, query):
        if not self.index:
            self.build_index()
        logging.debug('Docs; {}'.format(len(self.index)))

        words = [x.lower() for x in query.split()]

        words = [
            word
            for word in words
            if word not in self.stopwords]

        logging.debug('Query with ; {}'.format(words))

        all_words = [x.keys() for x in self.index.values()]
        all_words = chain.from_iterable(all_words)
        all_words = set(all_words)
        all_words = list(all_words)

        logging.debug('Unique indexed words; {}'.format(len(all_words)))

        scores = defaultdict(float)
        for page in self.index:
            for word in words:
                if word in self.index[page]:
                    scores[page] += self.index[page][word]

        logging.debug('Relevant documents; {}'.format(len(scores)))
        scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return scores


def main(filename):
    search_engine = TFIDF_JSON(filename)
    import sys
    if len(sys.argv) > 1:
        search_engine.build_index(sys.argv[1], num=None)
        search_engine.save_index()
    else:
        search_engine.load_index()

    # do the search function
    results = search_engine.search(input('Q? '))
    print()

    for result in results:
        print(result[0], '-->', result[1])


if __name__ == '__main__':
    main('index.json')
