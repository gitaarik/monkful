class Field(object):

    def serialize(self, *args, **kwargs):
        """
        Returns the serialized field.
        If it fails it will return `None`.
        """
        try:
            return self._serialize(*args, **kwargs)
        except:
            return None


class StringField(Field):

    def _serialize(self, v):
        return unicode(v)


class IntField(Field):

    def _serialize(self, v):
        return int(v)


class ListField(Field):

    def __init__(self, serializer):
        """
        Serializes a list of items using the provided serializer.
        """
        self.sub_serializer = serializer

    def _serialize(self, l):
        # Uses the `sub_serializer` to serialize the items in the list.
        return [self.sub_serializer().serialize(i) for i in l]


class BooleanField(Field):

    def _serialize(self, v):
        return bool(v)
