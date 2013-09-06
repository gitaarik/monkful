from monkful.resources import MongoEngineResource
from documents import Post
from serializers import PostSerializer


class PostResource(MongoEngineResource):
    document = Post
    serializer = PostSerializer
