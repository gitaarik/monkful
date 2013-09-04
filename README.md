# Monkful

Easily create RESTful API's for your MongoEngine documents. Inspired by Django
REST framework.

Monkful combines [Flank-RESTful](http://flask-restful.readthedocs.org/en/latest/)
and [MongoEngine](http://mongoengine.org/) and provides an easy way to create
RESTful resources for MongoEngine documents in a Flask project.

It's inspired by [Django REST framework](http://django-rest-framework.org/)'s
Views and Serializers.

## Development

Monkful is still very young and has few features. An advantage of this is that
it's easy to contribute. Contributions are very welcome.

## Installation

Make sure you have MongoDB installed and installed the requirements in
requirements.txt. Then include the source code of Monkful in your project
(as there is no pip package yet).

## A quick example

1. Create your MongoEngine documents:

    **documents.py**

    ```python
    from mongoengine import Document, fields

    class Post(Document):
        title = fields.StringField()
        text = fields.StringField()
    ```

2. Create serializers for your documents:

    **serializers.py**

    ```python
    from monkful.serializers import Serializer, fields

    class PostSerializer(Serializer):
        title = fields.StringField()
        text = fields.StringField()
    ```

3. Create resources for your documents by creating a `MongoEngineResource` object
and specifying the document and serializer:

    **resources.py**

    ```python
    from monkful.resources import MongoEngineResource
    from documents import Post
    from serializers import PostSerializer

    class PostResource(MongoEngineResource):
        document = Post
        serializer = PostSerializer
    ```

4. Make your resource available:

    **server.py**

    ```python
    from flask import Flask
    from flask.ext import restful
    from mongoengine import connect
    from resources import PostResource

    connect('posts')
    app = Flask(__name__)
    api = restful.Api(app)
    api.add_resource(PostResource, '/posts/')

    if __name__ == '__main__':
        app.run(debug=True)
    ```

5. Post something to your resource. Type this in your python shell when your
   env is activated:

    ```python
    import requests, json
    data = {'title': "Hello", 'text': "This is the content!"}
    requests.put('http://127.0.0.1:5000/posts/', data=json.dumps(data))
    ```

6. See the result: [http://127.0.0.1:5000/posts/](http://127.0.0.1:5000/posts/)
