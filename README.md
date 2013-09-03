# Monkful

Easily create RESTful API's using Flask and MongoEngine. Inspired by Django
REST framework.

Monkful combines [Flank-RESTful](http://flask-restful.readthedocs.org/en/latest/)
and [MongoEngine](http://mongoengine.org/) and provides an easy way to create
RESTful resources for MongoEngine documents in a Flask project.

It is inspired by [Django REST framework](http://django-rest-framework.org/)'s
use of Resources and Serializers.

## Development

Monkful is still very young and has few features. An advantage of this is that
it's easy to contribute. Contributions are very welcome too.

## A quick example

Put your MongoEngine documents in `documents.py`:

**documents.py**

    from mongoengine import Document, fields

    class Post(Document):
        title = fields.StringField()
        text = fields.StringField()

Create serializers for your documents in `serializers.py`:

**serializers.py**

    from monkful.serializers import Serializer, fields

    class PostSerializer(Serializer):
        title = fields.StringField()
        text = fields.StringField()

Create resources for your documents by creating a `MongoEngineResource` object
and specifying the document and serializer:

**resources.py**

    from monkful.resources import MongoEngineResource
    from documents import Post
    from serializers import PostSerializer

    class PostResource(MongoEngineResource):
        document = Post
        serializer = PostSerializer
