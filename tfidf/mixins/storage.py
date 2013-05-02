import os
import json
# import logging

from . import MixinSettings


class Storage(MixinSettings):
    def load_index(self):
        raise NotImplementedError()

    def save_index(self):
        raise NotImplementedError()


class JSON_Storage(Storage):
    def load_index(self):
        self.assert_has_arg('filename')
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
        self.assert_has_arg('filename')

        data = {
            "index": self.index,
            "metadata": self.mould_metadata()
        }
        with open(self.settings['filename'], 'w') as fh:
            json.dump(data, fh, indent=4)
