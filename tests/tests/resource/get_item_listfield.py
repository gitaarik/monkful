import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourceGetItemListField(unittest.TestCase):
    """
    Test the response of a HTTP GET request on a listfield from an item
    of a resource.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        article_id = "528a5250aa2649ffd8ce8a90"
        cls.initial_data = [
            {
                'text': "Test comment",
            },
            {
                'text': "Test comment 2",
            }
        ]

        # Load some initial data for this test case
        cls.data = {
            'articles': [
                {
                    'id': article_id,
                    'title': 'test',
                    'comments': cls.initial_data,
                }
            ]
        }

        for article in cls.data['articles']:
            Article(**article).save()

        cls.response = cls.app.get('/articles/{}/comments/'.format(article_id))

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

        # Delete the `id` and `date` field because those are not in the
        # intially set data.
        for comment in response_data:
            del(comment['id'])
            del(comment['date'])

        self.assertEqual(response_data, self.initial_data)
