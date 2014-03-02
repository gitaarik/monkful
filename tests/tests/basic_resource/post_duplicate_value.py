import unittest
import json
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourcePostDuplicateValue(unittest.TestCase):
    """
    Test if a HTTP POST request with a duplicate value for a unique
    field results in the correct response.
    """

    @classmethod
    def setUpClass(cls):

        server.app.debug = True
        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        # First manually put a post in the DB
        initial_data = {
            'title': "Test title",
            'text': "Test text"
        }

        Article(**initial_data).save()

        # Then POST an item with the same title (which should be unique)
        data = {
            'title': "Test title",
            'text': "Test text 2"
        }

        cls.response = cls.app.post(
            '/articles/',
            headers={'content-type': 'application/json'},
            data=json.dumps(data)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 409.
        """
        self.assertEqual(self.response.status_code, 409)

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
            self.fail("Response is not valid JSON.")

    def test_content(self):
        """
        Test if the response has a 'message'.
        """
        data = json.loads(self.response.data)
        self.assertTrue('message' in data)

    def test_documents(self):
        """
        Test if there's still only one document in the DB.
        """
        self.assertEqual(Article.objects.count(), 1)
