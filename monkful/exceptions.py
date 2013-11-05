class MonkfulError(Exception):
    pass


class InvalidQueryField(MonkfulError):

    def __init__(self, field, *args, **kwargs):
        self.message = "Invalid field in query: '{}'".format(field)
        super(InvalidQueryField, self).__init__(*args, **kwargs)
