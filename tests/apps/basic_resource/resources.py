from monkful.resources import MongoEngineResource
from documents import Article
from serializers import ArticleSerializer


class ArticleResource(MongoEngineResource):
    document = Article
    serializer = ArticleSerializer
