import os
import logging

from . import MixinSettings


class DirectorySource(MixinSettings):
    """
    takes the directory argument to the class
    and traverses it, yielding appropriate dictionaries
    """
    def documents(self, num=None):
        self.assert_has_arg('directory')
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


class WebsiteSource(MixinSettings):
    """
    takes url argument and traverses
    """
    def documents(self, num=None):
        self.assert_has_arg('url')
