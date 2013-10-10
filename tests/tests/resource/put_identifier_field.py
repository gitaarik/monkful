import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Article, Comment


class ResourcePutIdentifierField(unittest.TestCase):
    """
    Test if a HTTP PUT that updates a resource that has an embedded
    document with an identifier field which is used in the update gives
    the right response and updates the document correctly.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.initial_data = {
            'title': "Test title",
            'text': "Test text",
            'published': True,
            'comments': [
                Comment(text="Test comment "),
                Comment(text="Test comment 2"),
                Comment(text="Test comment 3"),
            ],
            'top_comment': Comment(text="Top comment")
        }

        cls.article = Article(**cls.initial_data).save()

        cls.comments_update = {
            'comments': [
                {
                    'id': unicode(cls.article['comments'][0]['id']),
                    'text': "Test comment update"
                },
                {
                    'id': unicode(cls.article['comments'][1]['id']),
                    'text': "Test comment update 2"
                }
            ]
        }

        cls.response = cls.app.put(
            '/articles/{}/'.format(unicode(cls.article['id'])),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.comments_update)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 200.
        """
        self.assertEqual(self.response.status_code, 200)

    def test_content_type(self):
        """
        Test if the content-type header is 'application/json'.
        """
        self.assertEqual(
            self.response.headers['content-type'],
            'application/json'
        )

    def test_json(self):
        """
        Test if the response data is valid JSON.
        """
        try:
            json.loads(self.response.data)
        except:
            self.fail("Respnose is not valid JSON.")

    def test_content(self):
        """
        Test if the deserialized response data evaluates back to our
        data we posted to the resource in `setUpClass`.
        """

        response_data = json.loads(self.response.data)

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        response_data = {
            'title': response_data['title'],
            'text': response_data['text'],
            'published': response_data['published'],
            'comments': [
                {
                    'id': response_data['comments'][0]['id'],
                    'text': response_data['comments'][0]['text']
                },
                {
                    'id': response_data['comments'][1]['id'],
                    'text': response_data['comments'][1]['text']
                }
            ],
            'top_comment': {
                'text': response_data['top_comment']['text']
            }
        }

        self.assertEqual(
            response_data,
            {
                'title': self.initial_data['title'],
                'text': self.initial_data['text'],
                'published': self.initial_data['published'],
                'comments': self.comments_update['comments'],
                'top_comment': {
                    'text': self.initial_data['top_comment']['text']
                }
            }
        )

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.initial_data['title'])
        self.assertEqual(article.text, self.initial_data['text'])
        self.assertEqual(
            article.comments[0].text,
            self.comments_update['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[1].text,
            self.comments_update['comments'][1]['text']
        )

        # The complete `comments` field should've been overwritten so
        # there should be only two comments instead of 3.
        self.assertEqual(len(article.comments), 2)

