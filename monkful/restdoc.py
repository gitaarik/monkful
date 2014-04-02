from .helpers import json_type


class RestDoc(object):
    """
    Generates a RestDoc for the given base_url and serializer.
    http://www.restdoc.org/
    """

    def __init__(self, resource):
        self.resource = resource

    def generate(self):

        return {
            'schemas': self.get_schemas(),
            'headers': self.get_headers(),
            'resources': self.get_resources()
        }

    def get_schemas(self):

        return {
            self.resource.get_base_url(): self.get_schema(
                self.resource.serializer
            )
        }

    def get_schema(self, serializer):

        return {
            'type': "inline",
            'schema': {
                'type': "object",
                'properties': self.get_schema_properties(serializer)
            }
        }

    def get_schema_properties(self, serializer):

        return {
            name: self.get_schema_properties_field(field)
            for name, field in serializer._fields().items()
        }

    def get_schema_properties_field(self, field):

        properties = {
            'type': json_type(field.deserialize_type),
            'description': field.description,
        }

        if field.readonly:
            properties['readonly'] = True
        elif field.writeonly:
            properties['writeonly'] = True

        if field.identifier:
            properties['identifier'] = True

        return properties

    def get_headers(self):
        return {
            'request': self.resource.request_headers(),
            'response': self.resource.response_headers()
        }

    def get_resources(self):
        return [
            {
                'id': self.resource.restdoc_name,
                'description': self.resource.restdoc_description,
                'path': self.resource.get_base_path(),
                'params': self.resource.restdoc_params,
                'methods': self.resource.restdoc_methods
            },
        ]
