class MonkfulError(Exception):
    pass


class InvalidQueryField(MonkfulError):

    def __init__(self, field, *args, **kwargs):
        self.field = field
        self.message = "Invalid field in query: '{}'".format(field)
        super(InvalidQueryField, self).__init__(*args, **kwargs)


class InvalidPageParamFormat(MonkfulError):

    def __init__(self, param, *args, **kwargs):
        self.param = param
        self.message = (
            "The param '{}' is an invalid identifier for a page".format(param)
        )
        super(InvalidPageParamFormat, self).__init__(*args, **kwargs)


class PageOutOfRange(MonkfulError):

    def __init__(self, param, *args, **kwargs):
        self.param = param
        self.message = (
            "The page '{}' is out of range".format(param)
        )
        super(PageOutOfRange, self).__init__(*args, **kwargs)
