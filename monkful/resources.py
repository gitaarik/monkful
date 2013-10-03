from flask import request
from flask.ext.restful import Resource, abort
from mongoengine import Document, fields
from mongoengine.errors import NotUniqueError, DoesNotExist, ValidationError

from .serializers import fields as serializer_fields
from .serializers.exceptions import (
    UnknownField, ValueInvalidType, DataInvalidType, DeserializeReadonlyField
)
from .helpers import json_type
from .exceptions import InvalidQueryField


class MongoEngineResource(Resource):

    def __init__(self, *args, **kwargs):
        # Instantiate the serializer
        self.serializer = self.serializer()
        super(MongoEngineResource, self).__init__(*args, **kwargs)

    def dispatch_request(self, *args, **kwargs):
        # Call authenticate for each request
        self.authenticate()
        self.check_request_content_type_header()
        return super(MongoEngineResource, self).dispatch_request(*args, **kwargs)

    def authenticate(self):
        """
        Placeholder for authenticating requests.

        If you want custom authentication, overwrite this method. If
        authentication fails, you should call `abort()` yourself (or
        something else you like).
        """
        return

    def check_request_content_type_header(self):
        """
        Checks if the content type header in the request is correct.
        """

        content_type = request.headers['content-type'].split(';')
        self.check_request_content_type(content_type[0].strip())

        if len(content_type) == 2:
            self.check_request_charset(content_type[1].strip())

    def check_request_content_type(self, content_type):
        """
        Checks if the content type (without the charset) in the request
        is correct.
        """

        if (
            request.method in ('POST', 'PUT') and
            content_type != 'application/json'
        ):

            abort(415, message=
                "Invalid Content-Type header '{}'. This resource "
                "only supports 'application/json'."
                .format(content_type)
            )

    def check_request_charset(self, charset):
        """
        Checks if the charset in the request is correct.
        """

        if charset != 'charset=utf-8':
            abort(415, message=
                "Invalid charset in Content-Type header '{}'. This resource "
                "only supports 'charset=utf-8'."
                .format(charset)
            )

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

        data = self.get_data(*args, **kwargs)

        if self.is_item(data):
            return self.get_item(data)
        else:
            return self.get_list(data)

    def is_item(self, data):
        """
        Returns `True` if `data` represents a single document and not a
        list of documents.

        By default it checks if it is an instance of a MongoEngine
        `Document`. If you use duck typing this could fail, in that case
        you could overwrite this method.
        """
        return isinstance(data, Document)

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

    def get_data(self, *args, **kwargs):
        """
        Returns the data that should be returned on GET requests.

        The default behaviour is:
        If there's an `id` parameter in the url variables it will try to
        find the document with that id and return that document.
        If there's a search query in the url it will try to find
        documents with that search query and return those.
        Else it will return all documents.

        You can overwrite this method to alter this behaviour.
        """

        if 'id' in kwargs:

            try:
                return self.document.objects.get(id=kwargs['id'])
            except (DoesNotExist, ValidationError):
                abort(404, message=
                    "The resource with id '{}' does not exist"
                    .format(kwargs['id'])
                )

        else:

            if request.args:
                return self.document.objects.filter(
                    **self._serialize_query(request.args.to_dict())
                )
            else:
                return self.document.objects

    def _serialize_query(self, query):
        """
        Validates and serializes the values provided in a search query.

        The idea is that the format for the search query is the same as
        a MongoEngine query:
        http://docs.mongoengine.org/en/latest/guide/querying.html
        However, operators haven't been implemented (yet).

        The values will automatically be deserialized.
        """

        new_query = {}

        for key, value in query.items():
            try:
                new_query[key] = self._deserialize_query_value(
                    key.split('__'), value
                )
            except InvalidQueryField:
                abort(400, message="Invalid query '{}'".format(key))

        return new_query

    def _deserialize_query_value(self, field_trace, value):
        """
        Returns the serialized `value` for the field specified by the
        `field_trace`.

        The `field_trace` should be a list of steps to the field. If its
        a field directly on the serializer it can be a list of one item:
        ['fieldname']
        But if it's a field inside an embedded document, the list would
        look like:
        ['embedded_doc_fieldname', 'fieldname']

        If the field doesn't exist on the serializer, it will raise an
        `InvalidQueryField` exception.
        """

        def deserialize_query_value(field_trace, serializer):
            """
            Will walk through the `field_trace` by calling itself
            recursively and return the deserialized value in the end.

            Will raise an `InvalidQueryField` exception when a field
            isn't found on the serializer.
            """

            # Pop first field from `field_trace`
            field = field_trace.pop(0)

            # Check if field exists on serializer
            if field in serializer._fields():

                # If there are still fields in the `field_trace` go on
                if field_trace:

                    serializer_field = serializer._field(field)

                    # If the field is a list field with a document
                    # field inside, recurse with the serializer from
                    # that document.
                    if (isinstance(
                        serializer_field,
                        serializer_fields.ListField
                    ) and isinstance(
                        serializer_field.sub_field,
                        serializer_fields.DocumentField
                    )):
                        return deserialize_query_value(
                            field_trace,
                            serializer_field.sub_field.sub_serializer
                        )

                    # If the field is a document field inside, recurse
                    # with the serializer from that document.
                    elif (isinstance(
                        serializer_field,
                        serializer_fields.DocumentField
                    )):
                        return deserialize_query_value(
                            field_trace,
                            serializer_field.sub_serializer
                        )

                    # Otherwise the trace was too deep and invalid
                    else:
                        raise InvalidQueryField(field)

                else:
                    # If there are no fields in the `field_trace` it
                    # means we found the serializer for the field, so
                    # return the deserialized value for it.
                    return serializer._field(field).deserialize(value)

            else:
                raise InvalidQueryField(field)

        return deserialize_query_value(field_trace, self.serializer)

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

        data = request.json

        if not data:
            abort(400, message="No data provided in request.")

        if request.method == 'POST':
            return self.process_request_data_post(data)
        elif request.method == 'PUT':
            return self.process_request_data_put(data)

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

        def create_document(document_type, values):
            return document_type(**values)

        def field_value(field, cur_value, data, serializer, parent=None):
            """
            Returns the value to use when updating `field` with `data`.
            """

            def listfield_value():
                """
                Returns the value to use when updating a list-field.

                Will loop through the items in `data` and get the value
                for the field by calling `field_value()` again. This way
                we build up a new list with the new field values.
                """

                new_value = []

                # Loop through the items in the `data`
                for item in data:

                    # Get the document's field instance for the field
                    # encapsuled inside the list-field.
                    field_item = field.field

                    # Set the parent field so children can get
                    # information about their parent, as is used in
                    # `documentfield_value()`.
                    item_parent = {
                        'field': field,
                        'value': cur_value
                    }

                    # Append the value for the field returned by
                    # `field_value()`.
                    new_value.append(
                        field_value(
                            field_item, None, item,
                            serializer.sub_field, item_parent
                        )
                    )

                return new_value

            def documentfield_value():
                """
                Returns the value to use when updating a document field.

                Either creates a new document or update a document based
                on the `identifier` field.

                Will check if the parent field is a ListField, if so,
                it will check if there's a `identifier` field on the
                serializer of the document, if so, it will try to find
                a matching document in the parent ListField (by
                checking if the `identifier` field matches), if it
                finds a matching document it will update this document
                instead of creating a new one.
                """

                doc_to_update = None

                # Check if there's a parent with a value that's an
                # instance of `ListField`.
                if (
                    parent and parent['value'] and
                    isinstance(parent['field'], fields.ListField)
                ):

                    # Loop through fields of the serializer of the document
                    for serializer_field in (
                        serializer.sub_serializer._fields().values()
                    ):

                        # Check if the serializer field has the option
                        # `identifier` set to `True`.
                        if serializer_field.identifier:

                            # Check if the `identifier` field is in
                            # `data`.
                            if serializer_field.name in data:

                                # Loop through the documents of the
                                # original list-field.
                                for document in parent['value']:

                                    # Check if the data matches this
                                    # document.
                                    if (
                                        data[serializer_field.name] ==
                                        getattr(
                                            parent['value'][0],
                                            serializer_field.name
                                        )
                                    ):
                                        # Set the document to update and
                                        # break out of the loop.
                                        doc_to_update = document
                                        break

                            # There can only be one `identifier` field, so
                            # we break out of this loop here.
                            break

                # If there's a document to update, update this document,
                # else create a new one.
                if doc_to_update:
                    return update_document(
                        doc_to_update,
                        data,
                        serializer.sub_serializer
                    )
                else:
                    return create_document(field.document_type, data)

            if field.__class__ in (
                fields.ListField,
                fields.SortedListField
            ):
                return listfield_value()
            elif field.__class__ in (
                fields.EmbeddedDocumentField,
                fields.GenericEmbeddedDocumentField,
                fields.ReferenceField,
                fields.GenericReferenceField
            ):
                return documentfield_value()
            else:
                return data

        def update_document(document, data, serializer):
            """
            Updates `document` with `data`.
            """

            for fieldname, field_data in data.items():

                # The document's field instance
                field = document._fields[fieldname]

                # The current value of the field
                cur_value = getattr(document, fieldname)

                # The serializer for the field
                field_serializer = getattr(serializer, fieldname)

                new_value = field_value(
                    field, cur_value, field_data, field_serializer
                )

                setattr(document, fieldname, new_value)

            return document

        return update_document(document, data, self.serializer)

    def _save_document(self, document):
        """
        Attempts to save the document.

        Will call `abort(400)` (which will trigger a Bad Request
        response) with an appropriate message if the document wasn't
        successfully saved.
        """

        try:
            self.save_document(document)
        except NotUniqueError:
            abort(409, message=
                "One or more fields are not unique. Please consult the scheme "
                "of the resource and ensure that you satisfy unique constraints."
            )
        except ValidationError, error:

            resource_errors = self._filter_validation_errors(error.errors)

            if resource_errors:
                abort(400, message="The data did not validate.", errors=resource_errors)
            else:
                # If there were no errors on resource fields, it means
                # the user of the resource can't help it, so it's a
                # server error, so we reraise the exception.
                raise

    def _filter_validation_errors(self, errors):
        """
        Filters validation errors from fields that are not defined on
        the serializers.

        This is for security. Users of the resource are allowed
        to see errors for fields in the resource, but not the other
        fields.
        """

        def filter_errors(errors, serializer, traceback=[]):
            """
            Filter `errors` based on the fields defined in `serializer`.
            """

            resource_errors = {}
            resource_fields = serializer._fields()

            for fieldname, fielderror in errors.items():

                if fieldname == '__all__':

                    # Ask `allow_document_validation_error()` if the
                    # Document wide error should be included.
                    if self.allow_document_validation_error(
                        fielderror, '.'.join(traceback)
                    ):
                        resource_errors[fieldname] = fielderror.message

                # Only include errors of fields that exist in the
                # serializer.
                elif fieldname in resource_fields:

                    item_traceback = traceback[:]
                    item_traceback.append(fieldname)

                    fielderror = field_error(
                        resource_fields[fieldname],
                        fielderror,
                        serializer,
                        item_traceback
                    )

                    # It could be that `field_error` returns something
                    # empty (because all the deeper errors of a
                    # DocumentField got filtered out), so check before
                    # we add it to our `resource_errors` dict.
                    if fielderror:
                        resource_errors[fieldname] = fielderror

            return resource_errors

        def field_error(field, error, serializer, traceback):
            """
            Returns the filtered `error` for the `field`.

            If the field is a `ListField` it will call `field_error()`
            for each item.

            If the field is a `DocumentField` it will call
            `filter_errors()` with it's `sub_serializer`.
            """

            if field.__class__ is serializer_fields.ListField:

                errors = []

                for sub_error in error.values():

                    sub_error = field_error(
                        field.sub_field, sub_error, serializer, traceback
                    )

                    if sub_error:
                        errors.append(sub_error)

                return errors

            elif field.__class__ is serializer_fields.DocumentField:
                return filter_errors(error, field.sub_serializer, traceback)
            else:
                return error.message

        return filter_errors(errors, self.serializer)

    def allow_document_validation_error(self, error, traceback):
        """
        This method receives document wide validation errors. It is
        called by `_filter_validation_errors` which filters out the
        field errors that don't exist on the resource (serializer).

        Because document wide errors could contain sensitive
        information, by default this method returns `False`, which
        means the error won't be shown in the response.

        You can however overwrite this method, inspect the `error` and
        `traceback` and decide you want to include this error in the
        response. In this case you would return `True` from this method.

        The traceback is a string of fieldnames seperated by dots. This
        indicates where the exception was raised.
        """
        return False

    def save_document(self, document):
        """
        Saves the provided document.

        Will be called by `_save_document()`. Monkful will automatically
        show Validation errors in the response if the fields the
        validation error is on exists in the resource. However, other
        validation errors will be raised and will result in a 500
        response.

        If it's necessary, you can overwrite this method to catch these
        exceptions, like this:

            def save_document(self, *args, **kwargs):

                try:
                    super(MyResource, self).save_document(*args, **kwargs)
                except ValidationError, error:
                    # do something with `error`
        """
        document.save()
