from monkful.serializers import Serializer, fields


class CommentSerializer(Serializer):
    id = fields.ObjectIdField(identifier=True)
    text = fields.StringField()
    date = fields.DateTimeField(readonly=True)


class ArticleSerializer(Serializer):
    title = fields.StringField()
    text = fields.StringField()
    comments = fields.ListField(fields.DocumentField(CommentSerializer))
    tags = fields.ListField(fields.StringField())
    top_comment = fields.DocumentField(CommentSerializer)
    publish = fields.BooleanField()
    publish_date = fields.DateTimeField()
