import sys
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
    '/articles/<path:path>'
)

if __name__ == '__main__':
    if 'shell' in sys.argv:
        from IPython import embed
        embed()
    else:
        app.run(debug=True)
