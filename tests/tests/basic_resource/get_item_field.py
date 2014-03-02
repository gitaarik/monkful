import unittest
import json
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourceGetItemField(unittest.TestCase):
    """
    Test the response of a HTTP GET request on a field from an item of a
    resource.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        article_id = "528a5250aa2649ffd8ce8a90"
        cls.initial_data = "Test title"

        # Load some initial data for this test case
        cls.data = {
            'articles': [
                {
                    'id': article_id,
                    'title': cls.initial_data
                }
            ]
        }

        for article in cls.data['articles']:
            Article(**article).save()

        cls.response = cls.app.get('/articles/{}/title/'.format(article_id))

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
            self.fail("Response is not valid JSON.")

    def test_content(self):
        """
        Test if the deserialized response data evaluates back to our
        initial data we inserted in `setUpClass`.
        """
        response_data = json.loads(self.response.data)
        self.assertEqual(response_data, self.initial_data)
