import os
import logging

__all__ = ['Source', 'DirectorySource']

_types = ['directory']


class Source(object):
    "simple template for Source object"
    def documents(self, num=None):
        raise NotImplementedError()


class DirectorySource(Source):
    """
    takes the directory argument to the class
    and traverses it, yielding appropriate dictionaries
    """
    def __init__(self, directory):
        self.directory = directory

    def documents(self, num=None):
        files = os.listdir(self.directory)

        files = (filename for filename in files if not filename == '.git')
        files = list(files[:num] if num else files)
        logging.info('Going to index {} items'.format(len(files)))

        for filename in files:
            filename = os.path.join(self.directory, filename)
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
