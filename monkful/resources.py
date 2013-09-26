import json
from flask import request
from flask.ext.restful import Resource, abort
from mongoengine import fields
from mongoengine.errors import NotUniqueError, DoesNotExist
from .serializers import fields as serializer_fields
from .serializers.exceptions import (
    UnknownField, ValueInvalidType, DataInvalidType, DeserializeReadonlyField
)
from .helpers import json_type


class MongoEngineResource(Resource):

    def __init__(self, *args, **kwargs):
        # Instantiate the serializer
        self.serializer = self.serializer()
        super(MongoEngineResource, self).__init__(*args, **kwargs)

    def dispatch_request(self, *args, **kwargs):
        # Call authenticate for each request
        self.authenticate()
        return super(MongoEngineResource, self).dispatch_request(*args, **kwargs)

    def authenticate(self):
        """
        Placeholder for authenticating requests.

        If you want custom authentication, overwrite this method. If
        authentication fails, you should call `abort()` yourself (or
        something else you like).
        """
        return

    def get(self, *args, **kwargs):
        """
        Handles a GET request.

        If `get_data()` returns a queryset, it will return a list of
        serialized documents from this queryset.

        If `get_data()` returns a document, it will return the
        serialized document.

        If `get_data()` returns something that evaluates to `False` it
        will raise a 404.
        """

        data = self.get_data()

        if not data:
            abort(404, "Not found")
        elif type(data) is list:
            return self.get_list(data)
        else:
            return self.get_item(data)

    def get_item(self, document):
        """
        Returns the provided MongoEngine document serialized.
        """
        return self.serializer.serialize(document)

    def get_list(self, queryset):
        """
        Returns a list of serialized documents from the provided
        MongoEngine queryset.
        """
        return [self.serializer.serialize(d) for d in queryset]

    def get_data(self):
        """
        Returns the data that should be returned on GET requests.

        The default behaviour is to return all the documents (by
        returning the MongoEngine queryset). You can overwrite this
        method to alter this behaviour.
        """
        return self.document.objects

    def post(self, *args, **kwargs):
        """
        Processes a HTTP POST request.

        Expects a JSON object that matches the serializer's fields or a
        JSON array of these objects.

        Returns the object/objects that was/were created, serialized
        into JSON format by the serializer.
        """

        request_data = self._request_data()

        if isinstance(request_data, list):
            # Process multiple documents

            documents = []

            for item in request_data:
                documents.append(self._process_document(item))

            # If we come here, it means `_process_document()` didn't
            # `abort()`, so the request data was not malformed, so we
            # can save the documents now.

            response = []
            for document in documents:
                self._save_document(document)
                response.append(self.serializer.serialize(document))

        else:
            document = self._process_document(request_data)
            self._save_document(document)
            response = self.serializer.serialize(document)

        return response, 201

    def put(self, *args, **kwargs):
        """
        Processes a HTTP PUT request.

        Will call `put_document()` to retreive the document that should
        be updated. If `put_document()` returns `None` it will create a
        new document instead of updating one.
        """

        put_document = self.put_document(*args, **kwargs)

        document = self._process_document(
            self._request_data(),
            document=put_document
        )
        self._save_document(document)
        response = self.serializer.serialize(document)

        if put_document:
            status_code = 200
        else:
            status_code = 201

        return response, status_code

    def put_document(self, *args, **kwargs):
        """
        Returns the document that will be updated on HTTP PUT methods.

        It will have the same parameters that are passed to the regular
        `put()` method.

        The default behaviour is to get the document based on the id
        supplied in the URL. This assumes that there is a URL endpoint
        in the form of `path_to_this_resource/<id>/`. If the id is not
        provided it will `abort()` with an appropriate error message.

        You can overwrite this method to alter the default behaviour.
        """
        try:
            document_id = kwargs['id']
        except KeyError:
            abort(400, message="No id provided")
        else:
            try:
                return self.document.get(id=document_id)
            except DoesNotExist:
                abort(404, message="Resource with id '{}' does not exist".format(id))

    def delete(self, id, *args, **kwargs):
        """
        Processes a HTTP DELETE request.
        If the document doesn't exist it will continue silently
        """
        try:
            self.document.objects.get(id=id).delete()
        except DoesNotExist:
            pass

        return {
            'details': "Successfully deleted document with id: {}".format(id)
        }

    def _request_data(self):
        """
        Returns the data in the HTTP request as a Python dict.

        If the data is not provided or is invalid JSON, it will
        `abort()` with an appropriate error message.
        """
        try:
            data = json.loads(request.data)
            if not data:
                abort(400, message="No data provided in request.")
            else:
                if request.method == 'POST':
                    return self.process_request_data_post(data)
                elif request.method == 'PUT':
                    return self.process_request_data_put(data)
        except ValueError:
            abort(400, message="Invalid JSON")

    def process_request_data_post(self, data):
        """
        Processes the JSON decoded data send by a POST request.

        By default nothing happens with the data and it is returned as
        is. You can however overwrite this method and add validation or
        change the data before returning it.

        If you add validation you should manually call `abort()` if the
        validation fails.
        """
        return self.process_request_data(data)

    def process_request_data_put(self, data):
        """
        Processes the JSON decoded data send by a PUT request.

        By default nothing happens with the data and it is returned as
        is. You can however overwrite this method and add validation or
        change the data before returning it.

        If you add validation you should manually call `abort()` if the
        validation fails.
        """
        return self.process_request_data(data)

    def process_request_data(self, data):
        """
        Processes the JSON decoded data send by a POST or PUT request.

        By default nothing happens with the data and it is returned as
        is. You can however overwrite this method and add validation or
        change the data before returning it.

        If you add validation you should manually call `abort()` if the
        validation fails.
        """
        return data

    def _process_document(self, data, document=None):
        """
        Creates a document with the supplied `data`.
        If `document` is provided, it will update this document instead.

        If the data doesn't validate, it will call `abort()` with an
        appropriate error message.
        """

        data = self._deserialize(data)

        # If we got here, there wasn't a deserialize error,
        # so we can safely update/create the document
        if document:
            return self._update_document(document, data)
        else:
            return self._create_document(data)

    def _deserialize(self, data):
        """
        Deserializes the data into a document.

        If there were exceptions during the deserialization, it will
        `abort` with an appropriate error message.
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

            return self.serializer.deserialize(data)

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

    def _create_document(self, data):
        """
        Creates a document with the provided data.
        Will return the created document.
        """
        return self.document(**data)

    def _update_document(self, document, data):
        """
        Updates the provided `document` with the provided `data`.

        The `data` should be a dict with the fieldnames as keys and the
        values as values. Also nested documents should be represented
        this way. Use a regular Python `list` for ListFields.
        """

        # There's no easy way to update a MongoEngine document using a
        # dict, so we have to loop through the `data` dict and update
        # the document manually. Also see:
        # http://stackoverflow.com/q/19002469/1248175

        def field_value(field, value):
            """
            Returns the value for the field as MongoEngine expects it.

            Takes `ListField` and `EmbeddedDocumentField` into account.
            """

            if field.__class__ in (fields.ListField, fields.SortedListField):
                return [
                    field_value(field.field, item)
                    for item in value
                ]
            if field.__class__ in (
                fields.EmbeddedDocumentField,
                fields.GenericEmbeddedDocumentField,
                fields.ReferenceField,
                fields.GenericReferenceField
            ):
                return field.document_type(**value)
            else:
                return value

        [setattr(
            document, key,
            field_value(document._fields[key], value)
        ) for key, value in data.items()]

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

            unique_fields = self._unique_fields_debug_info(document)

            if unique_fields:
                debug_info = (
                    " Note that these fields should be unique: {}."
                    .format(", ".join(unique_fields))
                )
            else:
                debug_info = ""

            message = (
                "A unique constraint on a field has been violated.{} If you "
                "keep having problems, please contact the system administrator."
                .format(debug_info)
            )
            abort(409, message=message)

    def _unique_fields_debug_info(self, document):
        """
        Returns information about unique fields on the resource.
        This is handy for debugging when a `NotUniqueError` is raised.
        """

        unique_fields = []

        def check_document(document, serializer=self.serializer, traceback=[]):
            """
            Checks if the provided document has fields with unique
            constraints. If so, it will add them to the `unique_fields`
            list.
            """

            for name, field in document._fields.items():
                # Only give info about fields that are on the serializer
                if name in serializer._fields().keys():
                    check_field(name, field, serializer, traceback)

        def check_field(name, field, serializer, traceback):
            """
            Checks if the provided field has a unique constraint, if so,
            it will add it to the `unique_fields` list.

            On encountering list or embedded document kind of fields, it
            will add their name into a traceback so the error message
            can show where the field exactly is.
            """

            if field.unique:

                if traceback:

                    traceback_msg = []

                    for item in traceback:
                        traceback_msg.append("{}".format(item['name']))

                    traceback_msg.insert(0, field.name)

                    unique_fields.append("'{}'".format(
                        "' in '".join(traceback_msg)
                    ))

                else:
                    unique_fields.append("'{}'".format(name))

            if field.__class__ in (fields.ListField, fields.SortedListField):

                check_field(
                    name, field.field,
                    serializer._fields()[name],
                    traceback
                )

            elif field.__class__ in (
                fields.EmbeddedDocumentField,
                fields.GenericEmbeddedDocumentField,
                fields.ReferenceField,
                fields.GenericReferenceField
            ):

                new_traceback = traceback[:]
                new_traceback.insert(0, {
                    'type': 'document',
                    'name': name,
                    'field': field
                })

                if serializer.__class__ == serializer_fields.ListField:
                    new_serializer = serializer.sub_type
                else:
                    new_serializer = serializer.fields()[name]

                check_document(
                    field.document_type,
                    new_serializer,
                    new_traceback
                )

        check_document(document)

        return unique_fields
