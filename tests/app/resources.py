from monkful.resources import MongoEngineResource
from documents import Post
from serializers import PostSerializer


class PostResource(MongoEngineResource):
    document = Post
    serializer = PostSerializer


class PostReadonlyResource(MongoEngineResource):
    document = Post
    serializer = PostSerializer
    allowed_methods = ('get',)


class PostWriteonlyResource(MongoEngineResource):
    document = Post
    serializer = PostSerializer
    blocked_methods = ('get',)
