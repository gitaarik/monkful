# Monkful

Easily create RESTful API's for your MongoEngine documents. Inspired by Django
REST framework.

Monkful combines [Flask-RESTful](http://flask-restful.readthedocs.org/en/latest/)
and [MongoEngine](http://mongoengine.org/) and provides an easy way to create
RESTful resources for MongoEngine documents in a Flask project. It's inspired
by [Django REST framework](http://django-rest-framework.org/)'s Views and
Serializers (in Monkful **Recources** and Serializers).

## Features

* Easy to set up RESTful API's based on MongoEngine documents
* POST multiple objects in one HTTP request
* Correct HTTP status codes and user friendly error messages on incorrect HTTP
  requests

## Development

Monkful is still very young and has few features. An advantage of this is that
it's easy to contribute. Contributions are very welcome!

## Installation

There's no pip yet so you'll have to manually add the code to your project.
Make sure you have MongoDB installed and installed the requirements in
requirements.txt.

## A quick example

Here is a quick example on how you can use Monkful. The magic happens in step
2 (`serializers.py`) and 3 (`resources.py`). This example is also available in
the `example/` directory. If you clone the project, create a virtualenv,
install the `requirements.txt` and run `python server.py` in the `example/`
directory you can play around with it.

1. Create a [MongoEngine document](http://docs.mongoengine.org/en/latest/tutorial.html#defining-our-documents):

    **documents.py**

    ```python
    from mongoengine import Document, fields

    class Post(Document):
        title = fields.StringField()
        text = fields.StringField()
    ```

2. Create a **Monkful** serializer for your document:

    **serializers.py**

    ```python
    from monkful.serializers import Serializer, fields

    class PostSerializer(Serializer):
        title = fields.StringField()
        text = fields.StringField()
    ```

3. Create a **Monkful** resource for your document by implementing
   `MongoEngineResource` and specifying the document and serializer:

    **resources.py**

    ```python
    from monkful.resources import MongoEngineResource
    from documents import Post
    from serializers import PostSerializer

    class PostResource(MongoEngineResource):
        document = Post
        serializer = PostSerializer
    ```

4. Make your resource available like a regular
   [Flask-RESTful resource](http://flask-restful.readthedocs.org/en/latest/quickstart.html#resourceful-routing):

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

5. Run the server:

    ```bash
    python server.py
    ```

6. Post something to your resource. Type this in your python shell when your
   env is activated:

    ```python
    import requests, json
    data = {'title': "Hello", 'text': "This is the content!"}
    requests.put('http://127.0.0.1:5000/posts/', data=json.dumps(data))
    ```

7. See the result: [http://127.0.0.1:5000/posts/](http://127.0.0.1:5000/posts/)
