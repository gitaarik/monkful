import json
from flask import request
from flask.ext.restful import Resource, abort
from .serializers.exceptions import (
    UnknownField, ValueInvalidType, DataInvalidType
)
from .helpers import json_type


class MongoEngineResource(Resource):

    def __init__(self, *args, **kwargs):
        # Instantiate the serializer
        self.serializer = self.serializer()
        super(MongoEngineResource, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Returns a list of serialized MongoEngine document objects.
        """
        return [self.serializer.serialize(d) for d in self.document.objects]

    def post(self, *args, **kwargs):
        """
        Processes a HTTP POST request.

        Expects a JSON object that matches the document's fields or a
        JSON array of these objects.

        Returns the object/objects that was/were created, serialized by
        the serializer.
        """

        try:
            data = json.loads(request.data)
        except:
            abort(400, message='Invalid JSON')

        multiple = isinstance(data, list)
        result = self._process_data(data, multiple)

        if multiple:

            response = []

            for document in result:
                document.save()
                response.append(self.serializer.serialize(document))

        else:
            result.save()
            response = self.serializer.serialize(result)

        return response, 201

    def _process_data(self, data, multiple):
        """
        Processes the data supplied to a POST or PUT request.

        Will call `abort(400)` (which will trigger a Bad Request
        response) with an appropriate message if the data doesn't
        validate.
        """

        def parent_traceback(parents):
            """
            Returns a traceback of the parents of the field, so it's
            clear on which field exactly the error occurred.

            For example, if the parents where two fields that were named
            'comments' and 'posts', this method will return:
                in 'comments' in 'posts'

            If there are no parents it will return an empty string
            """
            if parents:
                return " in '{}'".format(
                    "' in '".join(
                        [parent.name for parent in error.parents]
                    )
                )
            else:
                return ''

        try:

            if multiple:
                result = self._create_documents(data)
            else:
                result = self._create_document(data)

        except UnknownField, error:

            abort(400, message=
                "There is no field '{}'{} on this resource."
                .format(error.fieldname, parent_traceback(error.parents)))

        except ValueInvalidType, error:

            message = (
                "The value for field '{}'{} is of type '{}' but should be of "
                "type '{}'."
                .format(
                    error.field.name,
                    parent_traceback(error.parents),
                    json_type(error.value),
                    json_type(error.field.deserialize_type)
                )
            )

            abort(400, message=message)

        except DataInvalidType, error:

            if error.parents:

                parents = list(error.parents)
                field = parents.pop()

                message = (
                    "The value for field '{}'{} is of type '{}' but should be "
                    "of type 'Object'."
                    .format(
                        field.name,
                        parent_traceback(parents),
                        json_type(error.data)
                    )
                )

            else:
                message = "Invalid JSON."

            abort(400, message=message)

        return result

    def _create_documents(self, data_list):
        """
        Creates a document for each item in the provided list.
        Will return the list of created documents.
        """
        return [self._create_document(data) for data in data_list]

    def _create_document(self, data):
        """
        Creates a document with the provided data.
        Will return the created document.
        """
        return self.document(**self.serializer.deserialize(data))
