import sys
# import logging
# logging.info = print
# logging.debug = print
# logging.warning = print

from tfidf.core import TFIDF
from tfidf.mixins import DirectorySource, JSON_Storage


class TFIDF_JSON_FROM_DIRECTORY(DirectorySource, JSON_Storage, TFIDF):
    pass


def main(filename):
    directory = sys.argv[1] if sys.argv[1:] else None
    search_engine = TFIDF_JSON_FROM_DIRECTORY(
        index=filename, directory=directory)
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
    print('Displaying top {} results'.format(limit))

    for order, result in enumerate(results[:limit]):
        print('{}. {} --> {}'.format(order, result[0], result[1]))


if __name__ == '__main__':
    main('index.json')
