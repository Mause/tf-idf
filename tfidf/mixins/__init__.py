import types


class MixinSettings(object):
    def __init__(self, tfidf_object, **kwargs):
        self.settings = kwargs
        self.tfidf_object = tfidf_object

        functions = [
            getattr(self, attr) for attr in dir(self)
            if attr.startswith('_setup')
        ]

        functions = filter(
            lambda x: isinstance(x, types.MethodType),
            functions)

        for function in functions:
            function()

    def assert_has_arg(self, argument):
        msg = 'did you pass a valid {} argument to the constructor?'.format(argument)
        assert argument in self.settings and self.settings[argument], msg
