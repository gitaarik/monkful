import copy
import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourcePutCreateListFieldItem(unittest.TestCase):
    """
    Test if a HTTP PUT that creates an item in a listfield gives the
    right response and creates the item in the document.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        article_id = "528a5250aa2649ffd8ce8a90"
        comment_id = "528a5250aa2649ffd8ce8a91"

        # Load some initial data for this test case
        cls.initial_data = {
            'articles': [
                {
                    'id': article_id,
                    'title': "Test title",
                    'text': "Test text",
                    'publish': True,
                    'publish_date': datetime(2013, 10, 9, 8, 7, 8),
                    'comments': [
                        {
                            'id': comment_id,
                            'text': "Test comment",
                            'email': "test@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "1.2.3.4",
                                    'name': "Whoaa"
                                },
                                {
                                    'ip_address': "2.3.4.5",
                                    'name': "Nothis"
                                }
                            ]
                        },
                        {
                            'text': "Test comment 2",
                            'email': "test2@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "3.4.5.6",
                                    'name': "Zwarz"
                                },
                                {
                                    'ip_address': "4.5.6.7",
                                    'name': "Takada"
                                }
                            ]
                        }
                    ],
                    'top_comment': {
                        'text': "Top comment",
                        'upvotes': [
                            {
                                'ip_address': "5.6.7.8",
                                'name': "Warundro"
                            },
                            {
                                'ip_address': "6.7.8.9",
                                'name': "HWQOOO"
                            }
                        ]
                    },
                    'tags': ['test', 'unittest', 'python', 'flask']
                }
            ]
        }

        for article in cls.initial_data['articles']:
            Article(**article).save()

        cls.put_data = {'name': "Jawohl"}
        cls.put_ip_address = '5.5.5.5'

        cls.response = cls.app.put(
            '/articles/{}/comments/{}/upvotes/{}/'.format(
                article_id, comment_id, cls.put_ip_address
            ),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.put_data)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 201.
        """
        self.assertEqual(self.response.status_code, 201)

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

        del(response_data['date'])

        self.assertEqual(
            response_data,
            {
                'ip_address': self.put_ip_address,
                'name': self.put_data['name']
            }
        )

    def test_added(self):
        """
        Test if the item is really added to the document in the
        database.
        """

        self.assertEqual(
            len(Article.objects[0].comments[0].upvotes),
            3
        )

        self.assertEqual(
            Article.objects[0].comments[0].upvotes[2].name,
            self.put_data['name']
        )
