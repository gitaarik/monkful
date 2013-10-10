from bson import ObjectId
from mongoengine import Document, EmbeddedDocument, fields


class Comment(EmbeddedDocument):
    id = fields.ObjectIdField(default=ObjectId)
    text = fields.StringField()


class Article(Document):
    title = fields.StringField(unique=True)
    text = fields.StringField()
    comments = fields.ListField(fields.EmbeddedDocumentField(Comment))
    top_comment = fields.EmbeddedDocumentField(Comment)
    published = fields.BooleanField()
