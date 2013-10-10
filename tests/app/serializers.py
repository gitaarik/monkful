from monkful.serializers import Serializer, fields


class CommentSerializer(Serializer):
    id = fields.ObjectIdField(identifier=True)
    text = fields.StringField()


class ArticleSerializer(Serializer):
    title = fields.StringField()
    text = fields.StringField()
    comments = fields.ListField(fields.DocumentField(CommentSerializer))
    top_comment = fields.DocumentField(CommentSerializer)
    published = fields.BooleanField()
