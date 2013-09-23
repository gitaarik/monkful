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
* Assign fields as readonly or writeonly

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

## Documentation

### Serializers

In order to represent the data from your MongoEngine documents in an API, the
data from the documents should be serialized into a format that can be
transferred over HTTP. As a format, JSON has become the de facto standard, and
it's the only format Flask-RESTful currently supports, so that automatically
makes it the only format Monkful uses too.

As a small example for serialization: Consider you have a `DateTimeField` on a
MongoEngine document. MongoEngine stores Python `datetime` objects, however,
you can't include this in a JSON object of course. Besides that, JSON has no
datetime format of it's own.

In Monkful you specify a serializer on your resource. The serializer is
responsible for converting the MongoEngine document into a JSON object. On the
serializer you specify what fields should use what kind of serialization. For
example, for a MongoEngine `DateTimeField` you would use the Monkful field
serializer `DateTimeField` (which indeed happens to be the same name). This
field serializer will convert the python `datetime` object to an
[ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) string. That string will
then end up in the JSON object.

When a POST is done on a Monkful resource, it will expect a string in ISO 8601
format for a field with a `DateTimeField` field serializer. It will then
**deserialize** this string into a Python `datetime` object before it's
passed on to MongoEngine.

The idea is that Monkful will provide appropriate serializers for all standard
MongoEngine fields. Not all standard MongoEngine fields are covered yet, so if
you miss something, you're very welcome to contribute. If you created custom
MongoEngine fields, you can create custom Monkful field serializers for them.

#### Field serializers

This is a list of the field serializers Monkful currently supports. You can
import the fields using `from monkful.serializers import fields` and then use
for example `my_string_field = fields.StringField()` on your serializer.

The column "Appropriate for these MongoEngine fields" lists some MongoEngine
fields that this field serializer can be used for, however it's not necessarily
restricted to this field serializer. It is possible that there are several
field serializers that can be appropriate to use for a certain MongoEngine
field.

<table>
    <tr>
        <th>Monkful field serializer</th>
        <th>Appropriate for MongoEngine fields</th>
        <th>Arguments</th>
    <tr>
        <td>StringField</td>
        <td>
            <ul>
                <li>StringField</li>
                <li>URLField</li>
                <li>EmailField</li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>IntField</td>
        <td>
            <ul>
                <li>IntField</li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>BooleanField</td>
        <td>
            <ul>
                <li>BooleanField</li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>DateTimeField</td>
        <td>
            <ul>
                <li>DateTimeField</li>
                <li>ComplexDateTimeField</li>
            </ul>
        </td>
        <td></td>
    </tr>
    <tr>
        <td>DocumentField</td>
        <td>
            <ul>
                <li>EmbeddedDocumentField</li>
                <li>GenericEmbeddedDocumentField</li>
                <li>DictField</li>
                <li>MapField</li>
                <li>ReferenceField</li>
            </ul>
        </td>
        <td>
            <ul>
                <li>sub_serializer - The serializer to use for the object held by the field.</li>
            </ul>
        </td>
    </tr>
    <tr>
        <td>ListField</td>
        <td>
            <ul>
                <li>ListField</li>
                <li>SortedListField</li>
            </ul>
        </td>
        <td>
            <ul>
                <li>sub_serializer - The serializer to use for the objects in the list.</li>
            </ul>
        </td>
    </tr>
</table>

##### Global options

These options are available on all field serializers. You can provide these
options as keyword arguments to the serializer field's `__init__()` method.

* `readonly` - If set to `True` this field will only be readable. So on a `GET`
    request it will show up in the response, but if you try to supply the field
    in a `POST` or `PUT`, it will return an error.
* `writeonly` - If set to `True` this field will only be writable. So if you
    supply this field in a `POST` or `PUT` it will succeed, but the field won't
    show up in the response (as well as in the response of a `GET` request).
    This is handy for password fields where you want to be able to update a
    password but not expose it in the API.
