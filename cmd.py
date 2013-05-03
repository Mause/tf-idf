import os
import sys
import logging
logging.info = print
logging.debug = print

from tfidf.core import TFIDF
from tfidf.mixins.storage import JSON_Storage
from tfidf.mixins.source import DirectorySource


class TFIDF_JSON_FROM_DIRECTORY(DirectorySource, JSON_Storage, TFIDF):
    pass


def do_keyword(engine):
    doc = input()
    scores = engine.determine_keywords(doc)
    for score in scores:
        print(' *', score, scores[score])


def setup(filename):
    directory = sys.argv[1] if sys.argv[1:] else None
    engine = TFIDF_JSON_FROM_DIRECTORY(
        filename=filename, directory=directory)
    if len(sys.argv) > 1:
        engine.build_index()
        logging.info('Index built. Saving index')
        engine.save_index()
        logging.info('Saved. Size on disk is {:.2f}MB'.format(
            os.stat(filename).st_size / 1024 / 1024))
    else:
        logging.info('Loading index, with size of {:.2f}MB'.format(
            os.stat(filename).st_size / 1024 / 1024))
        engine.load_index()
        logging.info('Index loaded. {} words in index'.format(len(engine.index)))

    assert engine.index_loaded

    return engine


def do_search(engine):
    limit = 100
    # do the search
    results = engine.search(input('Q? '))

    keys_to_display = list(results.keys())[:limit]
    offset = max(map(len, [key.split('\\')[-1] for key in keys_to_display]))

    print()
    if results:
        print('Displaying top {} results'.format(limit))

        for key in keys_to_display:
            result = results[key]
            print('{} == {} --> {} --> {} --> {}'.format(
                key.split('\\')[-1].ljust(offset),
                str(result['score']).ljust(18),
                result['words_contained'],
                result['diff'],
                result['original']))
    else:
        print('No results')


if __name__ == '__main__':
    engine = setup('index.json')
    do_search(engine)
