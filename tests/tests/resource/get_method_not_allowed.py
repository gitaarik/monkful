import unittest
import json
from pymongo import MongoClient
from app import server


class ResourceGetMethodNotAllowed(unittest.TestCase):
    """
    Test if a HTTP POST request to a resource that only allows GET gives the
    right response.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        cls.response = cls.app.get('/posts-writeonly/')

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.post.remove()

    def test_status_code(self):
        """
        Test if the response status code is 201.
        """
        self.assertEqual(self.response.status_code, 403)

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
        self.assertEqual(data['error_code'], 'method_not_allowed')
