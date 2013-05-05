import os
import logging

from . import MixinSettings


class Source(MixinSettings):
    def documents(self, num=None):
        raise NotImplementedError()


class DirectorySource(Source):
    """
    takes the directory argument to the class
    and traverses it, yielding appropriate dictionaries
    """
    def documents(self, tfidf_object, num=None):
        self.assert_has_arg('directory')
        files = os.listdir(self.settings['directory'])

        files = (filename for filename in files if not filename == '.git')
        files = list(files[:num] if num else files)
        logging.info('Going to index {} items'.format(len(files)))

        for filename in files:
            filename = os.path.join(self.settings['directory'], filename)
            if not os.path.isdir(filename):
                with open(filename) as fh:
                    content = fh.read()

                if content:
                    # we dont want empty documents :P
                    yield {
                        "identifier": filename,
                        "content": content,
                        "metadata": {}
                    }


# class WebsiteSource(MixinSettings):
#     """
#     takes url argument and traverses
#     """
#     def documents(self, num=None):
#         self.assert_has_arg('url')
