import os
import sys
import time
import logging
logging.info = print
logging.debug = print

from tfidf.core import TFIDF
from tfidf.mixins.source import DirectorySource
from tfidf.mixins.sink import DatabaseSink, JSON_Sink


class TFIDF_JSON_FROM_DIRECTORY(DirectorySource, JSON_Sink, TFIDF):
    pass


class TFIDF_DB_FROM_DIRECTORY(DirectorySource, DatabaseSink, TFIDF):
    pass


TFIDF = TFIDF_DB_FROM_DIRECTORY or TFIDF_JSON_FROM_DIRECTORY


def setup(filename):
    directory = sys.argv[1] if sys.argv[1:] else None
    engine = TFIDF_JSON_FROM_DIRECTORY(
        filename=filename,
        directory=directory,
        database_file='db.db')
    if len(sys.argv) > 1:
        engine.build_index()
        logging.info('Index built. Saving index')
        t = time.time()
        engine.save_index()
        logging.info('Saved. Took {} seconds. Size on disk is {:.2f}MB'.format(
            time.time() - t,
            os.stat(filename).st_size / 1024 / 1024))
    else:
        logging.info('Loading index, with size of {:.2f}MB'.format(
            os.stat(filename).st_size / 1024 / 1024))
        t = time.time()
        engine.load_index()
        logging.info('Index loaded, took {} seconds. {} words in index'.format(
            time.time() - t,
            len(engine.index)))

    assert engine.index_loaded, 'wut?!'

    return engine


def do_keyword(engine):
    doc = input('\n> ')
    scores = engine.determine_keywords(doc)
    offset = max(map(len, scores.keys())) + 2
    for score in scores:
        print(' *', score.ljust(offset), scores[score])


def do_search(engine):
    limit = 50
    doc = input('\nQ? ')

    # do the search
    results = engine.search(doc)

    print()

    if results:
        keys_to_display = list(results.keys())[:limit]
        offset = max(map(len, [key.split('\\')[-1] for key in keys_to_display]))
        print('Displaying top {} results'.format(limit))

        for key in keys_to_display:
            result = results[key]
            print('{} == {:.5f} --> {:.5f} --> {:.2f} --> {}'.format(
                key.split('\\')[-1].ljust(offset),
                result['score'],
                result['original'],
                result['diff'],
                result['words_contained']
            ))
    else:
        print('No results')


if __name__ == '__main__':
    engine = setup('index.json')
    # do_keyword(engine)
    do_search(engine)
