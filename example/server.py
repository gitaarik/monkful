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
