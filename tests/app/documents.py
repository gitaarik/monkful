from datetime import datetime
from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, fields


class Vote(EmbeddedDocument):
    ip_address = fields.StringField(unique=True)
    name = fields.StringField()
    date = fields.DateTimeField(default=datetime.now)


class Comment(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId)
    text = fields.StringField()
    date = fields.DateTimeField(default=datetime.now)
    email = fields.EmailField()
    upvotes = fields.ListField(fields.EmbeddedDocumentField(Vote))


class Article(Document):
    title = fields.StringField(unique=True)
    text = fields.StringField()
    comments = fields.ListField(fields.EmbeddedDocumentField(Comment))
    top_comment = fields.EmbeddedDocumentField(Comment)
    tags = fields.ListField(fields.StringField())
    publish = fields.BooleanField()
    publish_date = fields.DateTimeField()
