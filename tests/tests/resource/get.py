import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourceGet(unittest.TestCase):
    """
    Test the response of a HTTP GET request.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        # Load some initial data for this test case
        cls.data = {
            'articles': [
                {
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
            ]
        }

        for article in cls.data['articles']:
            Article(**article).save()

        cls.response = cls.app.get('/articles/')

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
        initial data we inserted in `setUpClass`.
        """

        response_data = json.loads(self.response.data)[0]

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        response_data = [{
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
        }]

        self.assertEqual(response_data, self.data['articles'])
