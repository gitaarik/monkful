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


class SingleValueField(Field):
    """
    Fields that only have one value.

    Will check if the field is set, if so, return the `_value()` of it, else
    return `None`.
    """

    def _serialize(self, value):
        if value:
            return self._value(value)
        else:
            return None


class StringField(SingleValueField):
    """
    A field containing a string.
    """

    def _value(self, value):
        return unicode(value)


class IntField(SingleValueField):
    """
    A field containing an integer.
    """

    def _value(self, value):
        return int(value)


class BooleanField(SingleValueField):
    """
    A field containing a boolean.
    """

    def _value(self, value):
        return bool(value)


class ListField(Field):
    """
    A field containing a list of other types.

    Will serialize every item in the list using the provided serializer.
    """

    def __init__(self, serializer):
        """
        Serializes a list of items using the provided serializer.
        """
        self.sub_serializer = serializer

    def _serialize(self, field_list):
        # Uses the `sub_serializer` to serialize the items in the list.
        return [self.sub_serializer().serialize(item) for item in field_list]
