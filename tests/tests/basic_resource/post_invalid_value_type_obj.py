import unittest
import json
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourcePostInvalidValueTypeObj(unittest.TestCase):
    """
    Test if a HTTP POST request with an invalid value for a specific
    field results in the correct response.
    """

    @classmethod
    def setUpClass(cls):

        server.app.debug = True
        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        data = {
            'title': "Test title",
            'text': {
                'test': "This is not correct"
            }
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
            self.fail("Response is not valid JSON.")

    def test_content(self):
        """
        Test if the response has a 'message'.
        """
        data = json.loads(self.response.data)
        self.assertTrue('message' in data)

    def test_documents(self):
        """
        Test if the documents are still empty.
        """
        self.assertEqual(Article.objects.count(), 0)
