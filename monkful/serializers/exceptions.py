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

        super(ValueInvalidType, self).__init__(message, field, *args, **kwargs)
