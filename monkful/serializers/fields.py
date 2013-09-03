import dateutil.parser


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

    def deserialize(self, *args, **kwargs):
        return self._deserialize(*args, **kwargs)


class SingleValueField(Field):
    """
    Fields that only have one value.
    """

    def _serialize(self, value):
        """
        Returns the serialized value of the field.

        Checks if the field is set, if so, return the `_serialize_value()` of
        it, else return `None`.
        """
        if value is not None:
            return self._serialize_value(value)
        else:
            return None

    def _deserialize(self, value):
        """
        Returns the deserialized value of the field.

        Checks if the field is set, if so, return the `_deserialize_value()` of
        it, else return `None`.
        """
        if value is not None:
            return self._deserialize_value(value)
        else:
            return None


class StringField(SingleValueField):
    """
    A field containing a string.
    """

    def _serialize_value(self, value):
        return unicode(value)

    def _deserialize_value(self, value):
        return unicode(value)


class IntField(SingleValueField):
    """
    A field containing an integer.
    """

    def _serialize_value(self, value):
        return int(value)

    def _deserialize_value(self, value):
        return int(value)


class BooleanField(SingleValueField):
    """
    A field containing a boolean.
    """

    def _serialize_value(self, value):
        return bool(value)

    def _deserialize_value(self, value):
        return bool(value)


class DateTimeField(SingleValueField):
    """
    A field containing a python datetime object.
    """

    def _serialize_value(self, value):
        return value.isoformat()

    def _deserialize_value(self, value):
        return dateutil.parser.parse(value)


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

    def _deserialize(self, field_list):
        # Uses the `sub_serializer` to deserialize the items in the list.
        return [self.sub_serializer().deserialize(item) for item in field_list]
