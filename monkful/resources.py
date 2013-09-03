import json
from flask import request
from flask.ext import restful


class MongoEngineResource(restful.Resource):

    def __init__(self, *args, **kwargs):
        # Instantiate the serializer
        self.serializer = self.serializer()
        super(MongoEngineResource, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Returns a list of serialized MongoEngine document objects.
        """
        return [self.serializer.serialize(d) for d in self.document.objects]

    def put(self, *args, **kwargs):
        """
        Receives PUT requests and inserts the data it into the document.

        Expects a JSON object that matches the document's fields. Also a list
        of JSON objects can be provided.

        Returns the object/objects that was/were created, serialized by the
        serializer.
        """

        data = json.loads(request.data)

        if isinstance(data, list):

            documents = []

            for item in data:
                documents.append(self._add_document(item))

            return documents

        else:
            return self._add_document(data)

    def _add_document(self, data):
        """
        Deserialize the provided data and create and save an instance of the
        document with this data.

        Returns the document serialized by the serializer.
        """
        data = self.serializer.deserialize(data)
        newdoc = self.document(**data)
        newdoc.save()
        return self.serializer.serialize(newdoc)
