from flask import request
from flask.ext.restful import Resource, abort
from werkzeug.exceptions import BadRequest
from mongoengine import Document, fields
from mongoengine.errors import NotUniqueError, DoesNotExist, ValidationError

from .serializers import fields as serializer_fields
from .serializers.exceptions import (
    UnknownField, ValueInvalidType, ValueInvalidFormat, DataInvalidType
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
        self._init_target(*args, **kwargs)

        return super(
            MongoEngineResource, self
        ).dispatch_request(
            *args, **kwargs
        )

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

            abort(415, message=(
                "Invalid Content-Type header '{}'. This resource "
                "only supports 'application/json'."
                .format(content_type)
            ))

    def check_request_charset(self, charset):
        """
        Checks if the charset in the request is correct.
        """

        if charset != 'charset=utf-8':
            abort(415, message=(
                "Invalid charset in Content-Type header '{}'. This resource "
                "only supports 'charset=utf-8'."
                .format(charset)
            ))

    def _init_target(self, *args, **kwargs):
        """
        Initiates the target document and target serializer.
        """

        self.target_path = []

        if 'path' in kwargs:

            self.target_path = kwargs['path'].split('/')

            # the last item is usually an empty entry (because it splits
            # on the last slash too) so if it's empty, pop it.
            if self.target_path and not self.target_path[-1]:
                self.target_path.pop()

        self.target_document_obj = self.document
        target_path = self.target_path[:]
        self.target_parent = None
        self.target_document = None
        self.is_base_document = True
        self.target_serializer = self.serializer
        self.base_document = self.get_base_document()

        if self.base_document:
            self.target_list = None
            self.target_document = self.base_document
        else:
            self.target_list = self.get_base_list()

        # Determines if the document should be created. If not `False`,
        # contains the value for the id for the new document.
        self.create = False

        # The key for the identifier field in case a document needs to
        # be created.
        self.create_identifier_field = 'id'

        if target_path:

            if not self.base_document:

                identifier = target_path[0]

                try:
                    self.base_document = self.get_base_document_for_identifier(
                        identifier
                    )
                except DoesNotExist:

                    if request.method == 'PUT':
                        # If method is PUT, it should create the resource
                        # at this location.
                        self.create = identifier
                    else:
                        abort(404, message=(
                            "The resource specified with identifier '{}' "
                            "could not be found".format(identifier)
                        ))

                except ValidationError:
                    abort(400, message=(
                        "The formatting for the identifier '{}' is invalid".format(
                            identifier
                        )
                    ))

                self.target_document = self.base_document
                self.target_list = None
                target_path.pop(0)

            if target_path:

                self.is_base_document = False
                self.create = False

                def init_deep_target(target_path, depth):

                    identifier = target_path[0]
                    depth += 1

                    if self.target_list:

                        identifier_field = None
                        self.target_serializer = (
                            self.target_serializer.sub_field.sub_serializer
                        )

                        for fieldname, field in (
                            self.target_serializer._fields().items()
                        ):
                            if field.identifier:
                                identifier_field = fieldname
                                identifier = field.deserialize(identifier)

                        if identifier_field:

                            for i, document in enumerate(self.target_list):
                                if getattr(document, identifier_field) == identifier:
                                    self.target_parent_document = None
                                    self.target_parent_list = self.target_list
                                    self.target_document = self.target_list[i]
                                    self.target_list = None
                                    self.target_document_obj = (
                                        self.document.comments.field.document_type
                                    )
                                    break

                            if not self.target_document:

                                if request.method == 'PUT' and len(target_path) == 1:
                                    self.create = target_path[0]
                                    self.create_identifier_field = identifier_field
                                    self.target_document_obj = self.target_document_obj.field.document_type
                                else:
                                    abort(404, message=(
                                        "The resource specified with identifier '{}' could not be "
                                        "found".format(identifier)
                                    ))

                        else:

                            abort(404, message=(
                                "The resource specified with identifier '{}' could not be "
                                "found".format(identifier)
                            ))

                    else:

                        try:
                            self.target_serializer = getattr(self.target_serializer, identifier)
                        except AttributeError:
                            abort(404, message=(
                                "The resource specified with identifier '{}' could not be "
                                "found".format(identifier)
                            ))

                        if isinstance(self.target_serializer, serializer_fields.DocumentField):
                            self.target_serializer = self.target_serializer.sub_serializer

                        self.target_document_obj = getattr(self.target_document_obj, identifier)

                        if isinstance(self.target_document_obj, fields.EmbeddedDocumentField):
                            self.target_document_obj = self.target_document_obj.document_type

                        self.target_parent_document = self.target_document
                        self.target_parent_list = None
                        self.target_list = None
                        self.target_document = getattr(self.target_document, identifier)

                        if isinstance(self.target_document_obj, fields.ListField):
                            self.target_list = self.target_document
                            self.target_document = None

                    target_path.pop(0)
                    if target_path:
                        init_deep_target(target_path, depth)

                init_deep_target(target_path, 0)

    def get_base_document(self):
        """
        Returns the base document.

        By default this is `None` because by default the base resource
        returns a list of documents (returned by `get_base_list`).
        However, if this method returns a document, the base resource
        returns this document instead of a list.
        """
        return None

    def get_base_document_for_identifier(self, identifier):
        return (
            self.target_document_obj.objects.get(id=identifier)
        )

    def get_base_list(self):
        """
        Returns the base list of documents.

        By default it will return all the documents that are associated
        to the document Class `self.target_document`.

        You can overwrite this method to limit the base documents
        exposed in this resource.
        """
        return self.document.objects

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

        if self.target_list is None:

            return self.get_document_serialized(
                self.get_document(*args, **kwargs)
            )

        else:

            if self.is_base_document:
                return self.get_list_serialized(
                    self.get_list(*args, **kwargs)
                )
            else:
                return self.target_serializer.serialize(
                    self.get_list(*args, **kwargs)
                )

    def is_document(self, data):
        """
        Returns `True` if `data` represents a single document and not a
        list of documents.

        By default it checks if it is an instance of a MongoEngine
        `Document`. If you use duck typing this could fail, in that case
        you could overwrite this method.
        """
        return isinstance(data, Document)

    def get_document_serialized(self, document):
        """
        Returns the provided MongoEngine document serialized.
        """
        return self.target_serializer.serialize(document)

    def get_list_serialized(self, queryset):
        """
        Returns a list of serialized documents from the provided
        MongoEngine queryset.
        """
        return [self.target_serializer.serialize(d) for d in queryset]

    def get_document(self, *args, **kwargs):
        """
        Returns the document that should be returned on a GET request.
        """
        return self.target_document

    def get_list(self, *args, **kwargs):
        """
        Returns the list of documents that should be returned on a GET
        request.
        """
        if request.args:

            if self.is_base_document:
                return self._all_target_documents().filter(
                    **self._serialize_query(request.args.to_dict())
                )
            else:
                # TODO: make filters work for subdocuments
                return self._all_target_documents()

        else:
            return self._all_target_documents()

    def _all_target_documents(self):
        """
        Returns all documents that are exposed in this request.
        """
        # If the target document is the base document, use the
        # `get_base_list()` method, otherwise, use the `objects`
        # property, because target documents are subsets of the base
        # document and won't have to be limitted.
        if self.is_base_document:
            return self.get_base_list()
        else:
            return self.target_list

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

            # Ignore empty query params
            if not value:
                continue

            try:
                new_query[key] = self._deserialize_query_value(
                    key.split('__'), value
                )
            except InvalidQueryField:
                abort(400, message="Invalid query '{}'".format(key))

        return new_query

    def _deserialize_query_value(self, field_trace, value):
        """
        Returns the deserialized `value` for the field specified by the
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

        def url_decode_value(serializer_field, value):
            """
            Will decode the url value to the correct type corresponding
            to the given `serializer_field`.

            For example, if the `field` is an `IntField`, will cast the
            value to an int.
            """

            deserialize_type = serializer_field.deserialize_type

            if deserialize_type:
                return deserialize_type(value)
            else:
                return value

        def deserialize_query_value(field_trace, serializer, value):
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

                serializer_field = serializer._field(field)

                # If there are still fields in the `field_trace` go on
                if field_trace:

                    # If the field is a list field with a document
                    # field inside, recurse with the serializer from
                    # that document.
                    if (
                        isinstance(
                            serializer_field,
                            serializer_fields.ListField
                        )
                        and
                        isinstance(
                            serializer_field.sub_field,
                            serializer_fields.DocumentField
                        )
                    ):
                        return deserialize_query_value(
                            field_trace,
                            serializer_field.sub_field.sub_serializer,
                            value
                        )

                    # If the field is a document field inside, recurse
                    # with the serializer from that document.
                    elif (isinstance(
                        serializer_field,
                        serializer_fields.DocumentField
                    )):
                        return deserialize_query_value(
                            field_trace,
                            serializer_field.sub_serializer,
                            value
                        )

                    # Otherwise the trace was too deep and invalid
                    else:
                        raise InvalidQueryField(field)

                else:
                    # If there are no fields in the `field_trace` it
                    # means we found the serializer for the field, so
                    # return the deserialized value for it.

                    if isinstance(
                        serializer_field,
                        serializer_fields.ListField
                    ):
                        value = value.split(',')

                    return serializer_field.deserialize(
                        url_decode_value(serializer_field, value)
                    )

            else:
                raise InvalidQueryField(field)

        return deserialize_query_value(
            field_trace,
            self.target_serializer,
            value
        )

    def post(self, *args, **kwargs):
        """
        Processes a HTTP POST request.

        Expects a JSON object that matches the serializer's fields or a
        JSON array of these objects.

        Returns the object/objects that was/were created, serialized
        into JSON format by the serializer.
        """

        if self.target_list is None:
            # If the target is not at a list, then it's at an item, and
            # you can't update items with POST.
            abort(405, message=(
                "Can't update an item with POST, use PUT instead."
            ))

        request_data = self._request_data()

        if isinstance(request_data, list):
            # Process multiple documents

            response = []

            if self.is_base_document:

                documents = []

                for item in request_data:
                    documents.append(self._process_document(item))

                # If we come here, it means `_process_document()` didn't
                # `abort()`, so the request data was not malformed, so we
                # can save the documents now.

                for document in documents:
                    self._save_document(document)
                    response.append(self.target_serializer.serialize(document))

            else:

                new_documents = []

                for item in (
                    self.target_serializer.deserialize(request_data)
                ):
                    document = self.target_document_obj.field.document_type(
                        **item
                    )
                    new_documents.append(document)
                    self.target_list.append(document)

                self._save_document(self.base_document)
                response = self.target_serializer.serialize(new_documents)

        else:

            if self.is_base_document:
                document = self._process_document(request_data)
                self._save_document(document)
                response = self.target_serializer.serialize(document)
            else:
                document = self.target_document_obj.field.document_type(
                    **self.target_serializer.sub_field.deserialize(
                        request_data
                    )
                )
                self.target_list.append(document)
                self._save_document(self.base_document)
                response = self.target_serializer.sub_field.serialize(document)

        return response, 201

    def put(self, *args, **kwargs):
        """
        Processes a HTTP PUT request.

        Will call `put_document()` to retreive the document that should
        be updated. If `put_document()` returns `None` it will create a
        new document instead of updating one.
        """

        if self.target_document:
            put_document = self.target_document
        elif self.create:
            obj_params = {self.create_identifier_field: self.create}
            put_document = self.target_document_obj(**obj_params)
        else:
            abort(400, message="No id provided")

        if self.is_base_document:

            document = self._process_document(
                self._request_data(),
                document=put_document
            )
            self._save_document(document)
            response = self.target_serializer.serialize(document)

        else:

            document = self.target_document_obj(
                **self.target_serializer.deserialize(self._request_data())
            )

            for fieldname in document:

                if getattr(self.target_serializer, fieldname).identifier:
                    # Ignore the identifier field because we already
                    # have the values for him.
                    continue

                put_document[fieldname] = document[fieldname]

            if self.create:
                # If the document is new we still need to add this
                # document to the list.
                self.target_list.append(put_document)

            self._save_document(self.base_document)
            response = self.target_serializer.serialize(put_document)

        if self.create:
            status_code = 201
        else:
            status_code = 200

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
        return self.target_document

    def delete(self, *args, **kwargs):
        """
        Processes a HTTP DELETE request.
        """

        if not self.target_document:
            abort(400, message="No id provided")

        if self.is_base_document:
            self.target_document.delete()
        else:

            if self.target_parent_list:
                self.target_parent_list.remove(self.target_document)
                self._save_document(self.base_document)
            else:
                abort(400, message=(
                    "Can't delete a field. Maybe you want to update the "
                    "field to null?"
                ))

        return None, 204

    def _request_data(self):
        """
        Returns the data in the HTTP request as a Python dict.

        If the data is not provided or is invalid JSON, it will
        `abort()` with an appropriate error message.
        """

        try:
            data = request.json
        except BadRequest:
            abort(400, message="Request data is not valid JSON.")

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

        # If we got here, there wasn't a deserialize error,
        # so we can safely update/create the document
        if document:

            # Allow readonly fields because readonly fields can be
            # identifier fields. We need to have the identifier fields
            # to correctly update a resource.
            # `_update_document` will filter out the readonly fields
            # later on when updating the document.
            data = self._deserialize(data, allow_readonly=True)

            return self._update_document(document, data)

        else:
            return self._create_document(self._deserialize(data))

    def _deserialize(self, data, allow_readonly=False):
        """
        Deserializes the data into data appropriate for creating/
        updating a MongoEngine document.

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

            return self.target_serializer.deserialize(data, allow_readonly)

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

        except ValueInvalidFormat, error:

            message = (
                "The value '{}' for field '{}'{} could not be parsed. "
                "Note that it should be in {} format."
                .format(
                    error.value,
                    error.field.name,
                    parent_traceback(error.parents),
                    error.format_name
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

    def _create_document(self, data):
        """
        Creates a document with the provided data.
        Will return the created document.
        """
        return self.document(**data)

    def _update_document(
        self, document, data, serializer=None, update_lists=False
    ):
        """
        Updates the provided `document` with the provided `data`.

        The `data` should be a dict with the fieldnames as keys and the
        values as values. Also nested documents should be represented
        this way. Use a regular Python `list` for ListFields.
        """

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

                # Set the parent field so children can get
                # information about their parent, as is used in
                # `documentfield_value()`.
                item_parent = {
                    'field': field,
                    'value': cur_value
                }

                if update_lists and isinstance(
                    field.field, fields.EmbeddedDocumentField
                ):

                    identifier_field = None

                    for fieldname, item_field in (
                        serializer.sub_field.sub_serializer._fields().items()
                    ):
                        if item_field.identifier:
                            identifier_field = fieldname

                    if identifier_field:

                        for cur_value_item in cur_value:

                            keep_value = True

                            for item in data:
                                if (
                                    identifier_field in item and
                                    cur_value_item[identifier_field] ==
                                    item[identifier_field]
                                ):
                                    keep_value = False

                            if keep_value:
                                new_value.append(cur_value_item)

                # Loop through the items in the `data`
                for item in data:

                    # Append the value for the field returned by
                    # `field_value()`.
                    new_value.append(
                        field_value(
                            field.field, None, item,
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
                                            document,
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
                if not doc_to_update:
                    doc_to_update = field.document_type()

                return update_document(
                    doc_to_update,
                    data,
                    serializer.sub_serializer
                )

            if isinstance(field, fields.ListField):
                return listfield_value()
            elif isinstance(field, fields.EmbeddedDocumentField):
                return documentfield_value()
            else:
                return data

        def update_document(document, data, serializer):
            """
            Updates `document` with `data`.
            """

            for fieldname, field_data in data.items():

                # The serializer for the field
                field_serializer = getattr(serializer, fieldname)

                if field_serializer.readonly:
                    # Ignore readonly fields
                    continue

                # The document's field instance
                field = document._fields[fieldname]

                # The current value of the field
                cur_value = getattr(document, fieldname)

                new_value = field_value(
                    field, cur_value, field_data, field_serializer
                )

                setattr(document, fieldname, new_value)

            return document

        if not serializer:
            serializer = self.target_serializer

        return update_document(document, data, serializer)

    def _save_document(self, document):
        """
        Attempts to save the document.

        Will call `abort(400)` (which will trigger a Bad Request
        response) with an appropriate message if the document wasn't
        successfully saved.
        """

        try:
            document.save()
        except NotUniqueError, error:

            if self.allow_not_unique_error(error):

                abort(409, message=(
                    "One or more fields are not unique. Please consult "
                    "the scheme of the resource and ensure that you "
                    "satisfy unique constraints."),
                    error=unicode(error.message)
                )

            else:
                abort(409, message=(
                    "One or more fields are not unique. Please consult "
                    "the scheme of the resource and ensure that you "
                    "satisfy unique constraints."
                ))

        except ValidationError, error:

            resource_errors = self._filter_validation_errors(error.errors)

            if resource_errors:
                abort(
                    400,
                    message="The data did not validate.",
                    errors=resource_errors
                )
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

            if (
                field.__class__ is serializer_fields.ListField and
                # Listfields can have errors on the field itself or on
                # the field(s) inside it. If it has the method
                # `values()` we know it are multiple errors.
                hasattr(error, 'values')
            ):

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

        return filter_errors(errors, self.target_serializer)

    def allow_not_unique_error(self, error):
        """
        This method receives `NotUniqueError` exceptions. It is called
        by `_save_document()`. This method decides if the MongoDB error
        message that was raised can be shown in the response of the
        resource.

        For security reasons, this method returns `False` by default,
        so the error message won't be shown. If you want to allow this
        error message you can overwrite this method and return `True`.
        """
        return False

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
