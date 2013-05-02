import os
import sys
import json
import logging
from tfidf import TFIDF


logging.info = print
logging.debug = print
logging.warning = print


class DIRECTORY_SOURCE(object):
    def __init__(self, **kwargs):
        self.directory = kwargs['directory']
        return super(DIRECTORY_SOURCE, self).__init__(**kwargs)

    def documents(self, num=None):
        files = os.listdir(self.directory)

        files = (filename for filename in files if not filename == '.git')
        files = list(files[:num] if num else files)
        logging.info('Going to index {} items'.format(len(files)))

        for filename in files:
            filename = os.path.join(self.directory, filename)
            with open(filename) as fh:
                content = fh.read()

            yield {
                "identifier": filename,
                "content": content,
                "metadata": {}
            }


class JSON_STORAGE(object):
    def __init__(self, **kwargs):
        self.filename = kwargs['index']

        return super(JSON_STORAGE, self).__init__(**kwargs)

    def load_index(self):
        if not os.path.exists(self.filename):
            return {}
        # read in the index, if it is cached
        with open(self.filename) as fh:
            data = json.load(fh)
        self.index = data['index']
        self.index_metadata = data['metadata']
        self.index_loaded = True

    def save_index(self):
        assert self.index_loaded

        data = {
            "index": self.index,
            "metadata": self.mould_metadata()
        }
        with open(self.filename, 'w') as fh:
            json.dump(data, fh, indent=4)


class TFIDF_JSON_FROM_DIRECTORY(DIRECTORY_SOURCE, JSON_STORAGE, TFIDF):
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
