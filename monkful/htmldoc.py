import os
from flask import render_template_string
from helpers import json_type
from serializers import fields


class HtmlDoc(object):

    def __init__(self, resource):
        self.resource = resource

    def generate(self):

        template_path = '{}'.format(
            os.path.join(
                os.path.dirname(__file__),
                'templates',
                'htmldoc.html'
            )
        )

        with open(template_path) as f:
            template = f.read()

        context = {
            'name': self.resource.name,
            'fields': self.get_fields(self.resource.serializer),
            'sub_serializers': self.get_sub_serializers_info()
        }

        return render_template_string(template, **context)

    def get_sub_serializers_info(self):

        sub_serializers_info = {}
        sub_serializers = self.get_sub_serializers(self.resource.serializer)

        for name, serializer in sub_serializers.items():
            sub_serializers_info[name] = {
                'fields': self.get_fields(serializer)
            }

        return sub_serializers_info

    def get_sub_serializers(self, serializer):

        sub_serializers = {}

        for name, field in serializer._fields().items():

            sub_serializer = None

            if isinstance(field, fields.DocumentField):
                sub_serializer = field.sub_serializer
            elif isinstance(field, fields.ListField):
                sub_serializer = field.sub_field.sub_serializer

            if sub_serializer:

                sub_serializers[sub_serializer.name] = sub_serializer
                subsub_serializers = self.get_sub_serializers(sub_serializer)

                if subsub_serializers:
                    sub_serializers.update(subsub_serializers)

        return sub_serializers

    def get_fields(self, serializer):

        return {
            name: self.get_field(field)
            for name, field in serializer._fields().items()
        }

    def get_field(self, field):

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
