from flask import request
from flask.ext.restful import Resource, abort
from mongoengine import Document, EmbeddedDocument, fields
from mongoengine.base import BaseList
from mongoengine.errors import NotUniqueError, DoesNotExist, ValidationError
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
                "only supports 'application/json; charset=utf-8'."
                .format(request.headers['content-type'])
            )

    def check_request_charset(self, charset):
        """
        Checks if the charset in the request is correct.
        """

        if charset != 'charset=utf-8':
            abort(415, message=
                "Invalid charset in Content-Type header '{}'. This resource "
                "only supports 'application/json; charset=utf-8'."
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

        if not data:
            abort(404, message="Not found")
        elif self.is_item(data):
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

        The default behaviour is to return all the documents (by
        returning the MongoEngine queryset). You can overwrite this
        method to alter this behaviour.
        """

        try:
            document_id = kwargs['id']
        except KeyError:
            return self.document.objects
        else:
            return self.document.objects.get(id=document_id)

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


        #def create_document(document_type, values):
        #    return document_type(**values)

        #def field_value(cur_value, new_value):

        #    if isinstance(cur_value, BaseList):

        #        new_value = []

        #        for field_name, field_data in new_value:

        #            cur_value = None

        #            new_value.append(
        #                field_value(cur_value, field_data)
        #            )

        #        return new_value

        #    elif isinstance(cur_value, EmbeddedDocument):
        #        return create_document(new_value)
        #    else:
        #        return new_value


        #def update_document(document, data, serializer):

        #    for fieldname, field_data in data.items():
        #        cur_value = getattr(document, fieldname)
        #        new_value = field_value(cur_value, field_data)
        #        import ipdb; ipdb.set_trace()
        #        setattr(document, fieldname, new_value)

        #    return document

        #import ipdb; ipdb.set_trace()
        #document = update_document(document, data, self.serializer)

        #exit()

        return document

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
