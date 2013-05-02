import os
import json
import logging


class MixinSettings(object):
    def __init__(self, **kwargs):
        self.settings = kwargs


class DirectorySource(MixinSettings):
    """
    takes the directory argument to the class
    and traverses it, yielding appropriate dictionaries
    """
    def documents(self, num=None):
        assert 'directory' in self.settings and self.settings['directory'], 'did you pass a valid directory argument to the constructor?'
        files = os.listdir(self.settings['directory'])

        files = (filename for filename in files if not filename == '.git')
        files = list(files[:num] if num else files)
        logging.info('Going to index {} items'.format(len(files)))

        for filename in files:
            filename = os.path.join(self.settings['directory'], filename)
            with open(filename) as fh:
                content = fh.read()

            yield {
                "identifier": filename,
                "content": content,
                "metadata": {}
            }


class JSON_Storage(object):
    def load_index(self):
        assert 'filename' in self.settings and self.settings['filename'], 'did you provide a valid index filename?'
        if not os.path.exists(self.settings['filename']):
            return {}

        # read in the index, if it is cached
        with open(self.settings['filename']) as fh:
            data = json.load(fh)
        self.index = data['index']
        self.index_metadata = data['metadata']
        self.index_loaded = True

    def save_index(self):
        assert self.index_loaded
        assert 'filename' in self.settings and self.settings['filename'], 'did you provide a valid index filename?'

        data = {
            "index": self.index,
            "metadata": self.mould_metadata()
        }
        with open(self.settings['filename'], 'w') as fh:
            json.dump(data, fh, indent=4)
