import os
import sys
import time
import logging
logging.info = print
logging.debug = print

import tfidf.mixins.sink
from tfidf.core import TFIDF
from tfidf.mixins.source import DirectorySource


class TFIDF_JSON_FROM_DIRECTORY(DirectorySource, tfidf.mixins.sink.JSON_Sink, TFIDF):
    pass


class TFIDF_DB_FROM_DIRECTORY(DirectorySource, tfidf.mixins.sink.DatabaseSink, TFIDF):
    pass


def setup(settings):
    if settings['index_type'] == 'db':
        TFIDF = TFIDF_DB_FROM_DIRECTORY
        proper_filename = settings['database_filename']
    elif settings['index_type'] == 'json':
        TFIDF = TFIDF_JSON_FROM_DIRECTORY
        proper_filename = settings['index_filename']
    engine = TFIDF(**settings)

    if len(sys.argv) > 1:
        engine.build_index()
        logging.info('Index built. Saving index')
        t = time.time()
        engine.save_index()
        logging.info('Saved. Took {} seconds.'.format(time.time() - t))
    else:
        logging.info('Loading index')
        t = time.time()
        engine.load_index()
        logging.info('Index loaded, took {} seconds. {} words in index'.format(
            time.time() - t,
            len(engine.index)))

    logging.info('Size of index on disk is {:.2f}MB'.format(
        os.stat(proper_filename).st_size / 1024 / 1024))

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
    import argparse
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-d', '--directory', help='Directory to index. If not provided, uses prebuilt index', required=False)
    parser.add_argument('index_type', help='Method use to store index', choices=tfidf.mixins.sink._types)
    args = vars(parser.parse_args())

    directory = args.get('directory', None)
    args.update({
        "index_filename": 'index.json',
        "database_filename": 'db.db'
    })
    engine = setup(args)
    # do_keyword(engine)
    do_search(engine)
