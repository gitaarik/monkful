from ..exceptions import MonkfulError


class SerializerError(MonkfulError):

    def __init__(self, *args, **kwargs):

        # The parent types of the field the error occurred on.
        # An item can be a `Field` or a `Serializer`.
        self.parents = []

        super(SerializerError, self).__init__(*args, **kwargs)

    def add_parent(self, parent):
        """
        Add a parent type to the `self.parents` list.
        """
        self.parents.append(parent)


class DataInvalidType(SerializerError):

    def __init__(self, serializer, data, *args, **kwargs):

        # The serializer the error occurred on
        self.serializer = serializer

        # The data the serializer got
        self.data = data

        message = (
            "The data supplied to the serializer '{}' is of type '{}' but "
            "should be of type 'dict'."
            .format(
                serializer.__class__.__name__,
                type(data).__name__
            )
        )

        super(DataInvalidType, self).__init__(message, *args, **kwargs)


class FieldError(SerializerError):
    pass


class UnknownField(FieldError):
    """
    Raised when an unknown field is attempted to be accessed.
    """

    def __init__(self, fieldname, *args, **kwargs):

        # The name of the field that was attempted to be accessed.
        self.fieldname = fieldname

        message = (
            "The field '{}' was not found on the serializer."
            .format(fieldname)
        )

        super(UnknownField, self).__init__(message, *args, **kwargs)


class ValueInvalidType(FieldError):
    """
    Raised when an invalid type is supplied for a field.
    """

    def __init__(self, field, value, *args, **kwargs):

        # The field the error occurred on
        self.field = field

        # The value that was attempted to be inserted
        self.value = value

        message = (
            "The value for field '{}' is of type '{}' but should be of "
            "type '{}'."
            .format(
                field.name,
                type(value).__name__,
                field.deserialize_type.__name__
            )
        )

        super(ValueInvalidType, self).__init__(
            message, field, *args, **kwargs)


class ValueInvalidFormat(FieldError):
    """
    Raised when an invalid ISO date format is provided for a
    `DateTimeField`.
    """

    def __init__(self, field, format_name, value, *args, **kwargs):

        # The field the error occurred on
        self.field = field

        # The name of the format the value should be in
        self.format_name = format_name

        # The value that was attempted to be inserted
        self.value = value

        message = (
            "The value '{}' for field '{}' could not be parsed. "
            "Note that it should be in ISO 8601 format."
            .format(value, field.name)
        )

        super(ValueInvalidFormat, self).__init__(
            message, field, *args, **kwargs)


class SerializeWriteonlyField(FieldError):
    """
    Raised when a writeonly field is attempted to be serialized.
    """

    def __init__(self, field, *args, **kwargs):

        # The field the error occurred on
        self.field = field

        message = (
            "Can't serialize value for field '{}' because it's a writeonly "
            "field.".format(field.name)
        )

        super(SerializeWriteonlyField, self).__init__(
            message, field, *args, **kwargs)


class InvalidFieldSerializer(FieldError):
    """
    Raised when an invalid serializer is provided to a ListField.
    """

    def __init__(self, instance, serializer, *args, **kwargs):

        self.instance = instance
        self.serializer = serializer

        message = (
            "Invalid serializer '{}' provided to ListField '{}'. Note that "
            "ListField expects a FieldSerializer."
            .format(serializer, instance)
        )

        super(InvalidFieldSerializer, self).__init__(message, *args, **kwargs)
