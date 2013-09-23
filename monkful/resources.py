import json
from flask import request
from flask.ext.restful import Resource, abort
from mongoengine.errors import NotUniqueError, DoesNotExist
from mongoengine.base import BaseList, BaseDict
from .serializers.exceptions import (
    UnknownField, ValueInvalidType, DataInvalidType, DeserializeReadonlyField
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
        return [self.serializer.serialize(d) for d in self.documents()]

    def documents(self):
        return self.document.objects

    def post(self, *args, **kwargs):
        """
        Processes a HTTP POST request.

        Expects a JSON object that matches the document's fields or a
        JSON array of these objects.

        Returns the object/objects that was/were created, serialized by
        the serializer.
        """

        data = self._load_from_request(request)

        multiple = isinstance(data, list)
        doc_data = self._process_data(data, multiple)

        if multiple:

            response = []

            for document in doc_data:
                self._save_document(document)
                response.append(self.serializer.serialize(document))

        else:
            self._save_document(doc_data)
            response = self.serializer.serialize(doc_data)

        return response, 201

    def patch(self, id, *args, **kwargs):
        """
        Processes a HTTP PATCH request.

        Expects a JSON object that matches the document's fields or a
        JSON array of these objects.

        Additionally it needs an id in the URL that indicates which document to update.

        Returns the object/objects that was/were updated, serialized by
        the serializer.
        """

        data = self._load_from_request(request)

        try:
            document = self.document.objects.get(id=id)
        except DoesNotExist:
            abort(404, message="Document with id {} does not exist".format(id))

        doc_data = self._update_document(document, data, self.serializer)

        self._save_document(doc_data)
        response = self.serializer.serialize(doc_data)

        return response, 200

    def delete(self, id, *args, **kwargs):
        """
        Processes a HTTP DELETE request.
        If the document doesn't exist it will continue silently
        """
        try:
            self.document.objects.get(id=id).delete()
        except DoesNotExist:
            pass

        return {"details":"Successfully deleted document with id: {}".format(id)}, 200

    def _load_from_request(self, request):
        try:
            data = json.loads(request.data)
            if not data:
                abort(400, message="No data provided in request.")
            else:
                return data
        except ValueError:
            abort(400, message="Invalid JSON")

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

            message = (
                "There is no field '{}'{} on this resource."
                .format(error.fieldname, parent_traceback(error.parents))
            )

            abort(400, message=message)

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

        except DeserializeReadonlyField, error:

            message = (
                "The field '{}'{} is not writable as it is a readonly field."
                .format(
                    error.field.name,
                    parent_traceback(error.parents)
                )
            )

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

    def _update_document(self, document, data, serializer):
        """
        Loops over the incoming data and tries to set that data on document
        When it does it will use the serializer provided.
        Will call itself on sub-data when encountering lists and dicts
        """
        for key, value in data.iteritems():

            # When encountering lists or base lists we need to loop over the list
            # For each value we will call this function again.
            # The document for this call will be the item on the current document.
            # The data we want to set there is the value in the list we loop over
            # The serializer we need is the "sub_type" of the serializer under the 'key' in the current serializer
            if isinstance(value, BaseList) or isinstance(value, list):
                for index, list_value in enumerate(value):
                    self._update_document(document[key][index], list_value, getattr(serializer,key).sub_type)

            # When encountering dicts or base dicts we need loop over all items
            # For each item we will call this function again.
            # The document for this call will be the name of the item on the current document (as attribute or key).
            # The data we want to set there is the value of the item in the dict
            # The serializer we need is the "sub_serializer" of the serializer under the 'key' in the current serializer
            elif isinstance(value, BaseDict) or isinstance(value, dict):
                if hasattr(document, key):
                    self._update_document(getattr(document,key), value, getattr(serializer,key).sub_serializer)
                else:
                    self._update_document(document[key], value, getattr(serializer,key).sub_serializer)

            # When we encounter a base type we will try to set it on the document as an attribute.
            # We deserialize data before setting it
            # Read only fields are skipped.
            else:
                try:
                    deserialized = serializer._field(key).deserialize(value)
                    setattr(document, key, deserialized)
                except DeserializeReadonlyField:
                    continue

        return document

    def _save_document(self, document):
        """
        Attempts to save the document.

        Will call `abort(400)` (which will trigger a Bad Request
        response) with an appropriate message if the document wasn't
        successfully saved.
        """

        try:
            document.save()
        except NotUniqueError:

            unique_fields = [
                name
                for name, field in document._fields.items()
                if field.unique
            ]

            message = (
                "One of the values in the request is a duplicate on a unique "
                "field. Note that these fields should be unique: '{}'"
                .format("', '".join(unique_fields))
            )
            abort(409, message=message)
