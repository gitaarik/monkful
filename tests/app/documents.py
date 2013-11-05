from datetime import datetime
from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, fields


class Comment(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId)
    text = fields.StringField()
    date = fields.DateTimeField(default=datetime.now)


class Article(Document):
    title = fields.StringField(unique=True)
    text = fields.StringField()
    comments = fields.ListField(fields.EmbeddedDocumentField(Comment))
    tags = fields.ListField(fields.StringField())
    top_comment = fields.EmbeddedDocumentField(Comment)
    publish = fields.BooleanField()
    publish_date = fields.DateTimeField()
