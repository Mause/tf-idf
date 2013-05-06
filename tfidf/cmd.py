import time
import logging
logging.basicConfig(
    filename='tfidf.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s:%(levelname)s - %(filename)s:%(funcName)s:%(lineno)s - %(message)s'
)

from .core import TFIDF
from .ext.source import DirectorySource

from .ext.sink import _types as sink_types
from .ext.sink import JSON_Sink, DatabaseSink


def setup(settings):
    if settings['index_type'] == 'db':
        sink = DatabaseSink(settings['database_filename'])
    elif settings['index_type'] == 'json':
        sink = JSON_Sink(settings['index_filename'])

    source = DirectorySource(settings['directory']) if settings['directory'] else None

    engine = TFIDF(sink=sink, source=source, **settings)

    if settings['directory'] is not None:
        engine.build_index()
        print('Index built. Saving index')
        t = time.time()
        engine.save_index()
        print('Saved. Took {} seconds.'.format(time.time() - t))
    else:
        print('Loading index')
        t = time.time()
        engine.load_index()
        print('Index loaded, took {} seconds. {} words in index'.format(
            time.time() - t,
            len(engine.index)))

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
    parser.add_argument('-k', '--keywords', action='store_true', default=False)

    args = vars(parser.parse_args())

    args.update({
        "index_filename": 'index.json',
        "database_filename": 'db.db'
    })

    engine = setup(args)
    if args['keywords']:
        do_keyword(engine)
    else:
        do_search(engine)


if __name__ == '__main__':
    main()
