import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


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
            'posts': [
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
                    ]
                }
            ]
        }

        for post in cls.data['posts']:
            Post(**post).save()

        cls.response = cls.app.get('/posts/')

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.post.remove()

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
        self.assertEqual(
            json.loads(self.response.data),
            self.data['posts']
        )
