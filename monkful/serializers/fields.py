import inspect
import dateutil.parser
from bson.objectid import ObjectId
from .exceptions import (
    FieldError, ValueInvalidType, ValueInvalidFormat,
    SerializeWriteonlyField, InvalidFieldSerializer
)


class Field(object):

    # The type of of the `value` `deserialize()` expects to get.
    # If set to a Python type, will check if the value to
    # `deserialize()` is of this type and if not will raise a
    # `ValueInvalidType` exception.
    deserialize_type = None

    # A list of types that are allowed to typecast from. For example, a
    # FloatField should accept `int` types and typecast them to `float`.
    allowed_typecasts = []

    def __init__(self, **kwargs):

        # Name of the field
        self.name = None

        # If this field is a master field
        self.master = False

        # Description of the field
        self.description = kwargs.get('description')

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

    def _serialize(self, value):
        """
        By default returns the given `value` as is, but if a field needs
        special treatment for serializing the field subclass can
        overwrite this method.
        """
        return value

    def deserialize(self, value, allow_readonly=False):
        """
        Returns the deserialized value of the field.
        """

        if value is None:
            return None
        else:
            return self._deserialize(
                self.decode_value(value),
                allow_readonly=allow_readonly
            )

    def decode_value(self, value):
        """
        Checks if the given value is of the right type, if not, raises a
        `ValueInvalidType` exception, otherwise returns the value as is.
        """
        if self.deserialize_type:
            if (
                type(value) is not self.deserialize_type and
                type(value) not in self.allowed_typecasts
            ):
                raise ValueInvalidType(self, value)
            else:
                return self.deserialize_type(value)
        else:
            return value

    def _deserialize(self, value, **kwargs):
        """
        By default returns the given `value` as is, but if a field needs
        special treatment for deserializing the field subclass can
        overwrite this method.
        """
        return value

    def master_field(self):
        """
        Returns the master field for this field, if the field itself
        is the master field, it will return itself.

        The master field is a `Field` instance that is defined as an
        attribute on the serializer. Non-master fields are fields that
        are embedded in other fields, for example, in this serializer:

            class MySerializer(Serializer):
                scores = ListField(IntField())

        The `ListField` instance is a master field because it is defined
        as an attribute on the serializer, but the `IntField` is
        embedded inside this `ListField` and is therefore not a master
        field.
        """

        if self.master:
            return self
        else:
            return self.parent.master_field()


class StringField(Field):
    """
    A field containing a string.
    """
    deserialize_type = unicode


class IntField(Field):
    """
    A 32-bit integer field.
    """
    deserialize_type = int


class LongField(Field):
    """
    A 64-bit integer field.
    """

    # Just type `int`, because BSON doesn't have a long type:
    # http://bsonspec.org/#/specification
    #
    # MongoEngine's `LongField` maps to a 64-bit integer (instead of a
    # 32-bit integer for `IntField`).
    deserialize_type = int


class FloatField(Field):
    """
    A floating point number field.
    """
    deserialize_type = float
    allowed_typecasts = [int, long]


class BooleanField(Field):
    """
    A field containing a boolean.
    """
    deserialize_type = bool
    allowed_typecasts = [int]


class DateTimeField(Field):
    """
    A field containing a python datetime object.
    """

    deserialize_type = unicode

    def _serialize(self, value):
        return value.isoformat()

    def _deserialize(self, value, **kwargs):

        if value:

            try:
                return dateutil.parser.parse(value)
            except ValueError:
                raise ValueInvalidFormat(self, 'ISO 8601', value)

        else:
            return None


class DocumentField(Field):
    """
    A field containing a document.
    """

    deserialize_type = dict

    def __init__(self, sub_serializer, *args, **kwargs):

        self.sub_serializer = sub_serializer

        # Instantiate the `sub_serializer` if it's not yet an instance
        if inspect.isclass(self.sub_serializer):
            self.sub_serializer = self.sub_serializer()

        super(DocumentField, self).__init__(*args, **kwargs)

    def _serialize(self, data):
        return self.sub_serializer.serialize(data)

    def _deserialize(self, data, allow_readonly=False, **kwargs):

        try:
            return self.sub_serializer.deserialize(
                data,
                allow_readonly=allow_readonly
            )
        except FieldError as error:
            # If a `FieldError` exception occurs, we add this field as a
            # parent in the parent fields chain. This will be used for
            # error messages so that they can show what the parents of
            # the field are.

            error.add_parent(self.master_field())
            raise error


class ListField(Field):
    """
    A field containing a list of other fields.

    Will serialize every item in the list using the provided sub_field.
    """

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

    def _deserialize(self, field_list, allow_readonly=False, **kwargs):
        # Uses the `sub_serializer` to deserialize the items in the list
        return [
            self.sub_field.deserialize(item, allow_readonly=allow_readonly)
            for item in field_list
            if item is not None  # Don't allow `None` values in lists
        ]


class ObjectIdField(Field):
    """
    A field containing a MongoDB ObjectId.
    http://docs.mongodb.org/manual/reference/object-id/
    """

    readonly = True
    deserialize_type = unicode

    def _serialize(self, value):
        return unicode(value)

    def _deserialize(self, value, **kwargs):
        return ObjectId(value)


class DynamicField(Field):
    """
    A free form field which can hold any kind of value. Doesn't do any
    serializing/deserializing on the data.
    """

    deserialize_type = None


class ReferenceField(Field):
    """
    A field in which to store a reference id.
    """

    deserialize_type = unicode

    def _serialize(self, value):
        return unicode(value)
