import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


class ResourcePostInvalidJson(unittest.TestCase):
    """
    Test if a HTTP POST request with an invalid JSON payload gives the
    correct response.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        cls.response = cls.app.post('/posts/', data='thisisnojson')

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
        Test if the response has a 'message'.
        """
        data = json.loads(self.response.data)
        self.assertTrue('message' in data)

    def test_documents(self):
        """
        Test if the documents are still empty.
        """
        self.assertEqual(Post.objects.count(), 0)
