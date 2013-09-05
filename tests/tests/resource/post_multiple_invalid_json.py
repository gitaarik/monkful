import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


class ResourcePostMultipleInvalidJson(unittest.TestCase):
    """
    Test if a HTTP POST request providing multiple objects gives the
    right response and inserts the data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        data = [
            'this is not good',
            {
                'title': "Test title 2",
                'text': "Test text 2",
                'comments': [
                    {
                        'text': "Test comment 3"
                    },
                    {
                        'text': "Test comment 4"
                    }
                ]
            },
        ]

        cls.response = cls.app.post('/posts/', data=json.dumps(data))

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.post.remove()

    def test_status_code(self):
        """
        Test if the response status code is 400.
        """
        self.assertEqual(self.response.status_code, 400)

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

    def test_error_message(self):
        """
        Test if the correct error message is in the response.
        """
        data = json.loads(self.response.data)
        self.assertEqual(data['error_code'], 'invalid_json')

    def test_documents(self):
        """
        Test if the documents are still empty.
        """
        self.assertFalse(Post.objects.all())
