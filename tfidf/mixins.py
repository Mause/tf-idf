import os
import json
import logging


class DirectorySource(object):
    """
    takes the directory argument to the class
    and traverses it, yielding appropriate dictionaries
    """
    def __init__(self, **kwargs):
        self.directory = kwargs['directory']
        return super(DirectorySource, self).__init__()

    def documents(self, num=None):
        assert self.directory, 'did you pass a valid directory argument to the constructor?'
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


class JSON_Storage(object):
    def __init__(self, **kwargs):
        self.filename = kwargs['index']

        return super(JSON_Storage, self).__init__(**kwargs)

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
