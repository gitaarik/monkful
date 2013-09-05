from mongoengine import Document, EmbeddedDocument, fields


class Comment(EmbeddedDocument):
    text = fields.StringField()


class Post(Document):
    title = fields.StringField()
    text = fields.StringField()
    comments = fields.ListField(fields.EmbeddedDocumentField(Comment))
