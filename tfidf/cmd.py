import time
import logging
logging.info = print
logging.debug = print

from .core import TFIDF
from .mixins.source import DirectorySource

from .mixins.sink import _types as sink_types
from .mixins.sink import JSON_Sink, DatabaseSink


def setup(settings):
    if settings['index_type'] == 'db':
        settings['sink'] = DatabaseSink
    elif settings['index_type'] == 'json':
        settings['sink'] = JSON_Sink

    settings['source'] = DirectorySource

    engine = TFIDF(**settings)

    if settings['directory'] is not None:
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

    if hasattr(engine, 'index_size') and engine.index_size:
        logging.info('Size of index on disk is {:.2f}MB'.format(engine.index_size))

    assert engine.index_loaded, 'Subclass for sink has an implementation error'

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
        results_to_display = results[:limit]
        offset = max(map(len, [key[0].split('\\')[-1] for key in results_to_display]))
        print('Displaying top {} results'.format(limit))

        for key in results_to_display:
            result = key[1]
            print('{} == {:.5f} --> {:.5f} --> {:.2f} --> {}'.format(
                key[0].split('\\')[-1].ljust(offset),
                result['original'],
                result['score'],
                result['diff'],
                result['words_contained']
            ))
    else:
        print('No results')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-d', '--directory', help='Directory to index. If not provided, uses prebuilt index', required=False)
    parser.add_argument('index_type', help='Method use to store index', choices=sink_types)
    args = vars(parser.parse_args())

    args.update({
        "index_filename": 'index.json',
        "database_filename": 'db.db'
    })

    engine = setup(args)
    # do_keyword(engine)
    do_search(engine)


if __name__ == '__main__':
    main()
