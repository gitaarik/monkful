import inspect
import dateutil.parser
from .exceptions import UnknownField, ValueInvalidType, DataInvalidType


class Field(object):

    def __init__(self):
        # Name of the field
        self.name = None

    def serialize(self, *args, **kwargs):
        """
        Returns the serialized value of the field.
        If it fails it will return `None`.
        """
        return self._serialize(*args, **kwargs)

    def deserialize(self, *args, **kwargs):
        """
        Returns the deserialized value of the field.
        """
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

    # The type of value `_deserialize` expects to get
    deserialize_type = unicode

    def _serialize_value(self, value):
        return value

    def _deserialize_value(self, value):

        if type(value) is not unicode:
            raise ValueInvalidType(self, value)

        return value


class IntField(SingleValueField):
    """
    A field containing an integer.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = int

    def _serialize_value(self, value):
        return value

    def _deserialize_value(self, value):

        if type(value) is not int:
            raise ValueInvalidType(self, value)

        return value


class BooleanField(SingleValueField):
    """
    A field containing a boolean.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = bool

    def _serialize_value(self, value):
        return value

    def _deserialize_value(self, value):

        if type(value) is not bool:
            raise ValueInvalidType(self, value)

        return value


class DateTimeField(SingleValueField):
    """
    A field containing a python datetime object.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = unicode

    def _serialize_value(self, value):
        return value.isoformat()

    def _deserialize_value(self, value):

        if type(value) is not unicode:
            raise ValueInvalidType(self, value)

        return dateutil.parser.parse(value)


class ListField(Field):
    """
    A field containing a list of other types.

    Will serialize every item in the list using the provided serializer.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = list

    def __init__(self, sub_type):
        """
        Serializes a list of items using the provided `sub_type`. This
        can either be a `Serializer` or a `Field`.
        """

        self.sub_type = sub_type

        # Instantiate the `sub_type` if it's not yet an instance
        if inspect.isclass(sub_type):
            self.sub_type = self.sub_type()

    def _serialize(self, field_list):
        # Uses the `sub_serializer` to serialize the items in the list.
        return [self.sub_type.serialize(item) for item in field_list]

    def _deserialize(self, field_list):

        if type(field_list) is not list:
            raise ValueInvalidType(self, field_list)

        # Uses the `sub_serializer` to deserialize the items in the list.
        try:
            return [self.sub_type.deserialize(item) for item in field_list]
        except (UnknownField, ValueInvalidType, DataInvalidType) as error:
            error.add_parent(self)
            raise error
