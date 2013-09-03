import inspect
from .fields import Field


class Serializer(object):

    def serialize(self, document):
        """
        Returns serialized data for the provided document.

        Uses the field's `serialize` method to serialize the document's
        fields.
        """
        return {
            field: getattr(self, field).serialize(getattr(document, field))
            for field in self._fields()
        }

    def deserialize(self, data):

        data = {
            var: getattr(self, var).deserialize(value)
            for var, value in data.items()
        }

        return data

    def _fields(self):
        """
        Returns the fields on the serializer.

        It caches the fields so it won't have to inspect the serializer every
        time it's called.
        """
        try:
            return self.cached_fields
        except:
            self.cached_fields = {
                name: instance
                for name, instance in inspect.getmembers(self)
                if isinstance(instance, Field)
            }
            return self.cached_fields
