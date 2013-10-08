import inspect
import dateutil.parser
from bson.objectid import ObjectId
from .exceptions import (UnknownField, ValueInvalidType, DataInvalidType,
    SerializeWriteonlyField, InvalidFieldSerializer)


class Field(object):

    def __init__(self, **kwargs):

        # Name of the field
        self.name = None

        # If this is a read only field
        self.readonly = kwargs.get('readonly')

        # If this is a write only field
        self.writeonly = kwargs.get('writeonly')

        # If this field can act as an identifier for the document
        self.identifier = kwargs.get('identifier')

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

        if value:
            return dateutil.parser.parse(value)
        else:
            return None


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
    A field containing a list of other fields.

    Will serialize every item in the list using the provided sub_field.
    """

    # The type of value `_deserialize` expects to get
    deserialize_type = list

    def __init__(self, sub_field, *args, **kwargs):
        """
        Serializes a list of items using the provided `sub_field`.
        """

        # Explicitly check if the sub_field is an instance of `Field`
        # because it could be no problem here, but can be elsewhere.
        # For example, you could give a Document Serializer instead of a
        # DocumentField and it won't fail here because the serialize
        # method will do the same in both situations. However, when
        # inspecting the serializer, it's not expected to find a
        # Document Serializer on a ListField. Therefor the explicit
        # check.
        if not isinstance(sub_field, Field):
            raise InvalidFieldSerializer(self, sub_field, Field)

        self.sub_field = sub_field

        super(ListField, self).__init__(*args, **kwargs)

    def _serialize(self, field_list):
        # Uses the `sub_field` to serialize the items in the list
        return [self.sub_field.serialize(item) for item in field_list]

    def _deserialize(self, field_list):

        if type(field_list) is not list:
            raise ValueInvalidType(self, field_list)

        # Uses the `sub_serializer` to deserialize the items in the list
        try:
            return [self.sub_field.deserialize(item) for item in field_list]
        except (
            UnknownField,
            ValueInvalidType,
            DataInvalidType
        ) as error:
            # If any of these exceptions occur, we add this field as a
            # parent in the parent fields chain. This will be used for
            # debugging info.
            error.add_parent(self)
            raise error


class ObjectIdField(Field):
    """
    A field containing a MongoDB ObjectId.
    http://docs.mongodb.org/manual/reference/object-id/
    """
    readonly = True

    def _serialize(self, value):
        return unicode(value)

    def _deserialize(self, value):
        return ObjectId(value)
