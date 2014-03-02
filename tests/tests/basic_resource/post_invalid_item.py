import copy
import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourcePostInvalidItem(unittest.TestCase):
    """
    Test if a HTTP POST request on a specific item gives the right
    response.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        article_id = "528a5250aa2649ffd8ce8a90"

        cls.initial_data = {
            'id': article_id,
            'title': "Test title",
            'text': "Test text",
        }

        Article(**cls.initial_data).save()

        cls.data = {
            'title': "Test title updated",
            'text': "Test text updated",
        }

        cls.response = cls.app.post(
            '/articles/{}/'.format(article_id),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.data)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 405.
        """
        self.assertEqual(self.response.status_code, 405)

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
        data we posted to the resource in `setUpClass`.
        """

        response_data = json.loads(self.response.data)
        self.assertEqual(
            response_data,
            { 'message': "Can't update an item with POST, use PUT instead." }
        )

    def test_documents(self):
        """
        Test if the original data is still there.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.initial_data['title'])
        self.assertEqual(article.text, self.initial_data['text'])
