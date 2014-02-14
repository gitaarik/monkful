from monkful.serializers import Serializer, fields


class Vote(Serializer):
    ip_address = fields.StringField(identifier=True)
    date = fields.DateTimeField(readonly=True)


class CommentSerializer(Serializer):
    id = fields.ObjectIdField(identifier=True)
    text = fields.StringField()
    date = fields.DateTimeField(readonly=True)
    email = fields.StringField(writeonly=True)
    upvotes = fields.ListField(fields.DocumentField(Vote))


class ArticleSerializer(Serializer):
    id = fields.ObjectIdField(identifier=True)
    title = fields.StringField()
    text = fields.StringField()
    comments = fields.ListField(fields.DocumentField(CommentSerializer))
    tags = fields.ListField(fields.StringField())
    top_comment = fields.DocumentField(CommentSerializer)
    publish = fields.BooleanField()
    publish_date = fields.DateTimeField()
