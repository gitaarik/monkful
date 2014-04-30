import os
from operator import attrgetter
from copy import deepcopy

from markdown import markdown
from flask import render_template_string
from helpers import json_type
from serializers import fields


class HtmlDoc(object):
    """
    Generates a HTML page which describes the resource.
    """

    def __init__(self, resource):
        """
        Initiates the class with the given `resource`.
        """
        self.resource = resource

    def generate(self):
        """
        Generates a HTML page which describes the `self.resource`.
        """

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
            'description': markdown(self.resource.description),
            'params_info': self.get_params_info(),
            'fields': self.get_fields_info(self.resource.serializer),
            'sub_serializers': self.get_sub_serializers_info()
        }

        return render_template_string(template, **context)

    def get_sub_serializers_info(self):
        """
        Returns information about the sub serializers, formatted to be
        used in a template.
        """

        sub_serializers_info = {}
        sub_serializers = self.get_sub_serializers(self.resource.serializer)

        for name, serializer in sub_serializers.items():
            sub_serializers_info[name] = {
                'fields': self.get_fields_info(serializer)
            }

        return sub_serializers_info

    def get_sub_serializers(self, serializer):
        """
        Returns an array of sub serializers for the given `serializer`.
        """

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

    def get_fields_info(self, serializer):
        """
        Returns information about the fields of the given `serializer`,
        formatted to be used in a template.
        """
        fields = []
        [fields.append(field) for field in serializer._fields().values()]
        fields = sorted(fields, key=attrgetter('field_order'))
        return [self.get_field_info(field) for field in fields]

    def get_field_info(self, field):
        """
        Returns information about the given `field` formatted to be used
        in a template.
        """

        properties = {
            'name': field.name,
            'type': json_type(field.deserialize_type),
            'description': markdown(field.description),
        }

        if field.readonly:
            properties['readonly'] = True
        elif field.writeonly:
            properties['writeonly'] = True

        if field.identifier:
            properties['identifier'] = True

        return properties

    def get_params_info(self):
        """
        Returns information about the parameters of the resource,
        formatted to be used in a template.
        """

        if not self.resource.params_info:
            return None

        params_info = deepcopy(self.resource.params_info)

        for info in params_info:
            info['description'] = markdown(info['description'])

        return params_info
