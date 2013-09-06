from flask import Flask
from flask.ext import restful
from mongoengine import connect
from resources import PostResource, PostReadonlyResource, PostWriteonlyResource


connect('unittest_monkful')
app = Flask(__name__)
api = restful.Api(app)
api.add_resource(PostResource, '/posts/')
api.add_resource(PostReadonlyResource, '/posts-readonly/')
api.add_resource(PostWriteonlyResource, '/posts-writeonly/')

if __name__ == '__main__':
    app.run(debug=True)
