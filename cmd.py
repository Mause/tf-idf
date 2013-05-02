import sys
# import logging
# logging.info = print
# logging.debug = print

from tfidf.core import TFIDF
from tfidf.mixins.storage import JSON_Storage
from tfidf.mixins.source import DirectorySource


class TFIDF_JSON_FROM_DIRECTORY(DirectorySource, JSON_Storage, TFIDF):
    pass


def main(filename):
    directory = sys.argv[1] if sys.argv[1:] else None
    search_engine = TFIDF_JSON_FROM_DIRECTORY(
        filename=filename, directory=directory)
    if len(sys.argv) > 1:
        search_engine.build_index()
        print('Index built. Saving index')
        search_engine.save_index()
        print('Saved')
    else:
        print('Loading index')
        search_engine.load_index()
        print('Index loaded')

    limit = 10
    # do the search function
    results = search_engine.search(input('Q? '))

    keys_to_display = list(results.keys())[:limit]
    offset = max(map(len, keys_to_display))

    print()
    if results:
        print('Displaying top {} results'.format(limit))

        for key in keys_to_display:
            result = results[key]
            print('{} --> {}'.format(key.ljust(offset), result['score']))
    else:
        print('No results')


if __name__ == '__main__':
    main('index.json')
