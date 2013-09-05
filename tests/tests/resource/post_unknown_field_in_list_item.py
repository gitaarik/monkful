import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


class ResourcePostUnknownFieldInListItem(unittest.TestCase):
    """
    Test if a HTTP POST request with an unknown field in a list item
    gives the correct response.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.data = {
            'title': "Test title",
            'text': "Test text",
            'comments': [
                {
                    'text': "Test comment",
                    'unknown_field': "This field doesn't exist"
                },
                {
                    'text': "Test comment 2"
                }
            ]
        }

        cls.response = cls.app.post('/posts/', data=json.dumps(cls.data))

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.drop_database('unittest_monkful')

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
        self.assertEqual(data['message'], "There is no field 'unknown_field' in 'comments' on this resource.")

    def test_document(self):
        """
        Test if the documents are still empty.
        """
        self.assertFalse(Post.objects.all())
