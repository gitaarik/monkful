import inspect
from .fields import Field
from .exceptions import UnknownField, DataInvalidType


class Serializer(object):

    def __init__(self):

        self.field_cache = {}
        self.fields_cache = {}

        # Set names of fields on field instances
        for fieldname, field in self._fields().items():
            field.name = fieldname

    def serialize(self, document):
        """
        Returns serialized data for the provided document.

        Uses the field's `serialize` method to serialize the document's
        fields.
        """
        return {
            fieldname: field.serialize(getattr(document, fieldname))
            for fieldname, field in self._fields().items()
            if not field.writeonly
        }

    def deserialize(self, data):
        """
        Returns the given data deserialized.

        The data is expected to be a dict with the fieldname as the key
        and the fieldvalue as the value.

        The returned data is also a dictionary with this structure, only
        the values are deserialized by using the `deserialize` method on
        the field.
        """

        if type(data) is not dict:
            raise DataInvalidType(self, data)

        deserialized_data = {}

        for fieldname, value in data.items():

            field = self._field(fieldname)

            # Ignore read-only fields. For convenience we don't give an
            # error for this because otherwise clients need to strip out
            # the read-only fields when they modify data from a GET and
            # send it back through PUT.
            if not field.readonly:
                deserialized_data[fieldname] = field.deserialize(value)

        return deserialized_data

    def _field(self, fieldname):
        """
        Get the field on the serializer with the name `fieldname`.

        It will try to find the field on the serializer and validate
        that it's a `Field` instance. It will cache the result so
        subsequent call's on the same `fieldname` won't have this
        overhead.

        If the field is not found it will raise an `UnknownField`
        exception.
        """

        if fieldname in self.field_cache:
            field = self.field_cache[fieldname]
        else:

            try:
                field = getattr(self, fieldname)
            except AttributeError:
                field = None
            else:
                if not isinstance(field, Field):
                    field = None

            self.field_cache[fieldname] = field

        if not field:
            raise UnknownField(fieldname)
        else:
            return field


    def _fields(self):
        """
        Returns the fields on the serializer.

        It caches the fields so it won't have to inspect the serializer
        every time it's called.
        """

        if not self.fields_cache:

            self.fields_cache = {
                name: instance
                for name, instance in inspect.getmembers(self)
                if isinstance(instance, Field)
            }

        return self.fields_cache
