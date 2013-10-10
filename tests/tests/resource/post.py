import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourcePost(unittest.TestCase):
    """
    Test if a HTTP POST request gives the right response and inserts the
    data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.data = {
            'title': "Test title",
            'text': "Test text",
            'published': True,
            'comments': [
                {
                    'text': "Test comment"
                },
                {
                    'text': "Test comment 2"
                }
            ],
            'top_comment': {
                'text': "Top comment"
            }
        }

        cls.response = cls.app.post(
            '/articles/',
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.data)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 201.
        """
        self.assertEqual(self.response.status_code, 201)

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
                    'text': response_data['comments'][0]['text']
                },
                {
                    'text': response_data['comments'][1]['text']
                }
            ],
            'top_comment': {
                'text': response_data['top_comment']['text']
            }
        }

        self.assertEqual(response_data, self.data)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.data['title'])
        self.assertEqual(article.text, self.data['text'])
        self.assertEqual(
            article.comments[0].text,
            self.data['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[1].text,
            self.data['comments'][1]['text']
        )
