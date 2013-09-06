from monkful.serializers import Serializer, fields


class CommentSerializer(Serializer):
    text = fields.StringField()


class PostSerializer(Serializer):
    title = fields.StringField()
    text = fields.StringField()
    comments = fields.ListField(CommentSerializer)
    published = fields.BooleanField()
