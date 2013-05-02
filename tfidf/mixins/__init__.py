# from .source import *
# from .storage import *


class MixinSettings(object):
    def __init__(self, **kwargs):
        self.settings = kwargs

    def assert_has_arg(self, argument):
        msg = 'did you pass a valid {} argument to the constructor?'.format(argument)
        assert argument in self.settings and self.settings[argument], msg
