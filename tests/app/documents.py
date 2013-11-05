from datetime import datetime
from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, fields


class Comment(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId)
    text = fields.StringField()
    date = fields.DateTimeField(default=datetime.now)
    email = fields.EmailField()


class Article(Document):
    title = fields.StringField(unique=True)
    text = fields.StringField()
    comments = fields.ListField(fields.EmbeddedDocumentField(Comment))
    top_comment = fields.EmbeddedDocumentField(Comment)
    tags = fields.ListField(fields.StringField())
    publish = fields.BooleanField()
    publish_date = fields.DateTimeField()
