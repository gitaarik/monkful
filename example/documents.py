from mongoengine import Document, fields

class Post(Document):
    title = fields.StringField()
    text = fields.StringField()
