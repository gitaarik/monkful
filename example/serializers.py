from monkful.serializers import Serializer, fields

class PostSerializer(Serializer):
    title = fields.StringField()
    text = fields.StringField()
