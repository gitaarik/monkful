import inspect
import dateutil.parser
from .exceptions import (UnknownField, ValueInvalidType, DataInvalidType,
    SerializeWriteonlyField, DeserializeReadonlyField)


class Field(object):

    def __init__(self, readonly=False, writeonly=False):

        # Name of the field
        self.name = None

        # If this is a read only field
        self.readonly = readonly

        # If this is a write only field
        self.writeonly = writeonly

    def serialize(self, value):
        """
        Returns the serialized value of the field.
        If it fails it will return `None`.
        """

        if self.writeonly:
            raise SerializeWriteonlyField(self)

        if value is None:
            return None
        else:
            return self._serialize(value)

    def deserialize(self, value):
        """
        Returns the deserialized value of the field.
        """

        if self.readonly:
            raise DeserializeReadonlyField(self)

        if value is None:
            return None
        else:
            return self._deserialize(value)


class StringField(Field):
    """
    A field containing a string.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = unicode

    def _serialize(self, value):
        return value

    def _deserialize(self, value):

        if type(value) is not unicode:
            raise ValueInvalidType(self, value)

        return value


class IntField(Field):
    """
    A field containing an integer.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = int

    def _serialize(self, value):
        return value

    def _deserialize(self, value):

        if type(value) is not int:
            raise ValueInvalidType(self, value)

        return value


class BooleanField(Field):
    """
    A field containing a boolean.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = bool

    def _serialize(self, value):
        return value

    def _deserialize(self, value):

        if type(value) is not bool:
            raise ValueInvalidType(self, value)

        return value


class DateTimeField(Field):
    """
    A field containing a python datetime object.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = unicode

    def _serialize(self, value):
        return value.isoformat()

    def _deserialize(self, value):

        if type(value) is not unicode:
            raise ValueInvalidType(self, value)

        return dateutil.parser.parse(value)


class DocumentField(Field):
    """
    A field containing a document.
    """

    def __init__(self, sub_serializer, *args, **kwargs):

        self.sub_serializer = sub_serializer

        # Instantiate the `sub_serializer` if it's not yet an instance
        if inspect.isclass(self.sub_serializer):
            self.sub_serializer = self.sub_serializer()

        super(DocumentField, self).__init__(*args, **kwargs)

    def _serialize(self, data):
        return self.sub_serializer.serialize(data)

    def _deserialize(self, data):

        if type(data) is not dict:
            raise ValueInvalidType(self, data)

        return self.sub_serializer.deserialize(data)


class ListField(Field):
    """
    A field containing a list of other types.

    Will serialize every item in the list using the provided serializer.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = list

    def __init__(self, sub_type, *args, **kwargs):
        """
        Serializes a list of items using the provided `sub_type`. This
        can either be a `Serializer` or a `Field`.
        """

        self.sub_type = sub_type

        # Instantiate the `sub_type` if it's not yet an instance
        if inspect.isclass(self.sub_type):
            self.sub_type = self.sub_type()


        super(ListField, self).__init__(*args, **kwargs)

    def _serialize(self, field_list):
        # Uses the `sub_serializer` to serialize the items in the list.
        return [self.sub_type.serialize(item) for item in field_list]

    def _deserialize(self, field_list):

        if type(field_list) is not list:
            raise ValueInvalidType(self, field_list)

        # Uses the `sub_serializer` to deserialize the items in the list.
        try:
            return [self.sub_type.deserialize(item) for item in field_list]
        except (
            UnknownField,
            ValueInvalidType,
            DataInvalidType,
            DeserializeReadonlyField
        ) as error:
            error.add_parent(self)
            raise error
