from flask import Flask
from flask.ext import restful
from mongoengine import connect
from resources import ArticleResource


connect('unittest_monkful')
app = Flask(__name__)
api = restful.Api(app)
api.add_resource(
    ArticleResource,
    '/articles/',
    '/articles/<id>/',
    '/articles/<id>/<em_doc1>/'
)

if __name__ == '__main__':
    app.run(debug=True)
