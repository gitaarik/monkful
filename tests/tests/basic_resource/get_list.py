import copy
import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourceGetList(unittest.TestCase):
    """
    Test the response of a HTTP GET request on the listview of a
    resource.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        # Load some initial data for this test case
        cls.data = {
            'articles': [
                {
                    'title': "Test title",
                    'text': "Test text",
                    'publish': True,
                    'publish_date': datetime(2013, 10, 9, 8, 7, 8),
                    'comments': [
                        {
                            'text': "Test comment",
                            'email': "test@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "1.2.3.4",
                                },
                                {
                                    'ip_address': "2.3.4.5",
                                }
                            ]
                        },
                        {
                            'text': "Test comment 2",
                            'email': "test2@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "3.4.5.6",
                                },
                                {
                                    'ip_address': "4.5.6.7",
                                }
                            ]
                        }
                    ],
                    'top_comment': {
                        'text': "Top comment",
                        'upvotes': [
                            {
                                'ip_address': "5.6.7.8",
                            },
                            {
                                'ip_address': "6.7.8.9",
                            }
                        ]
                    },
                    'tags': ['test', 'unittest', 'python', 'flask']
                }
            ]
        }

        for article in cls.data['articles']:
            Article(**article).save()

        cls.response = cls.app.get('/articles/')

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

        response_data = json.loads(self.response.data)[0]

        # Check that the readonly field `date` in `comments` is present
        # and a valid date.
        for comment in response_data['comments']:
            try:
                parser.parse(comment['date'])
            except:
                self.fail(
                    "Could not parse the value `{}` into a date object "
                    "in `date` in `comments`."
                    .format(comment['date'])
                )

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        response_data = [{
            'title': response_data['title'],
            'text': response_data['text'],
            'publish': response_data['publish'],
            'publish_date': parser.parse(response_data['publish_date']),
            'comments': [
                {
                    'text': response_data['comments'][0]['text'],
                    'upvotes': [
                        {
                            'ip_address': (
                                response_data['comments'][0]
                                ['upvotes'][0]['ip_address']
                            ),
                        },
                        {
                            'ip_address': (
                                response_data['comments'][0]
                                ['upvotes'][1]['ip_address']
                            ),
                        },
                    ]
                },
                {
                    'text': response_data['comments'][1]['text'],
                    'upvotes': [
                        {
                            'ip_address': (
                                response_data['comments'][1]
                                ['upvotes'][0]['ip_address']
                            ),
                        },
                        {
                            'ip_address': (
                                response_data['comments'][1]
                                ['upvotes'][1]['ip_address']
                            ),
                        },
                    ]
                }
            ],
            'top_comment': {
                'text': response_data['top_comment']['text'],
                'upvotes': [
                    {
                        'ip_address': (
                            response_data['top_comment']
                            ['upvotes'][0]['ip_address']
                        ),
                    },
                    {
                        'ip_address': (
                            response_data['top_comment']
                            ['upvotes'][1]['ip_address']
                        ),
                    },
                ]
            },
            'tags': response_data['tags']
        }]

        # Remove `email` fields from the `comments` fields from the
        # initial data, because this field is a writeonly field and
        # shouldn't be exposed in the resource.
        initial_article = copy.deepcopy(self.data['articles'][0])
        for comment in initial_article['comments']:
            del(comment['email'])

        self.assertEqual(response_data, [initial_article])

        # Test if the field `email` in `comments` is not present,
        # because it's a writeonly field and shouldn't be exposed in the
        # resource.
        self.assertNotIn('email', response_data[0]['comments'])
