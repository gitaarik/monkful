import json
import random
import unittest
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourceGetListFilters(unittest.TestCase):
    """
    Test if an HTTP GET request on a listview with filters gives the
    right response.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        # Test filters on all field types:
        # - StringField
        # - BoolField
        # - IntField
        # - FloatField
        # - LongField
        # TODO: add more types to test
        cls.params = {
            'text': "This text should match",
            'publish': 1,
            'order': 333,
            'version': 2.5,
            'serial_number': 4581951951031539524
        }

        matching_articles = [
            {
                'title': "The first one",
                'text': cls.params['text'],
                'publish': True,
                'order': cls.params['order'],
                'version': cls.params['version'],
                'serial_number': cls.params['serial_number'],
            },
            {
                'title': "A sixt one",
                'text': cls.params['text'],
                'order': cls.params['order'],
                'publish': True,
                'version': cls.params['version'],
                'serial_number': cls.params['serial_number'],
            }
        ]

        non_matching_articles = []

        for i in range(100):

            # one divergent parameter should exclude the article
            exclude_match = random.choice(
                ('text', 'publish', 'order', 'version', 'serial_number')
            )

            title = "Non matching article #{}".format(i)

            if exclude_match == 'text':
                text = "Non matching text #{}".format(i)
            else:
                text = cls.params['text']

            if exclude_match == 'publish':
                publish = False
            else:
                publish = True

            if exclude_match == 'order':
                order = random.randint(0, 100)
            else:
                order = cls.params['order']

            if exclude_match == 'version':
                version = float('1.{}'.format(random.randint(0, 9)))
            else:
                version = cls.params['version']

            if exclude_match == 'serial_number':
                serial_number = random.randint(
                    1000000000000000000, 2000000000000000000
                )
            else:
                serial_number = cls.params['serial_number']

            non_matching_articles.append({
                'title': title,
                'text': text,
                'publish': publish,
                'order': order,
                'version': version,
                'serial_number': serial_number
            })

        # Load some initial data for this test case
        initial_data = matching_articles + non_matching_articles

        for article in initial_data:
            Article(**article).save()

        query_string = '?{}'.format(
            '&'.join([
                '{}={}'.format(key, value)
                for key, value in cls.params.items()
            ])
        )

        cls.response = cls.app.get('/articles/{}'.format(query_string))

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

    def test_results(self):
        """
        Test if the results match the filters.
        """

        response_data = json.loads(self.response.data)
        self.assertEqual(len(response_data), 2)

        for article in response_data:
            for key, value in self.params.items():
                self.assertEqual(article[key], value)
