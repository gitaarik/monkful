import json
import random
import unittest
from datetime import datetime
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


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
        cls.matching_values = {
            # StringField
            'text': "This text should match",

            # BoolField
            'publish': 1,

            # DateTimeField
            'publish_date': datetime(2010, 10, 5),

            # IntField
            'order': 333,

            # FloatField
            'version': 2.5,

            # LongField
            'serial_number': 4581951951031539524,

            # ListField
            'tags': ['matching_tag1', 'matching_tag2']
        }

        matching_articles = [
            {
                'title': "The first one",
                'text': cls.matching_values['text'],
                'publish': True,
                'publish_date': cls.matching_values['publish_date'],
                'order': cls.matching_values['order'],
                'version': cls.matching_values['version'],
                'serial_number': cls.matching_values['serial_number'],
                'tags': cls.matching_values['tags'],
                'top_comment': {}
            },
            {
                'title': "A sixt one",
                'text': cls.matching_values['text'],
                'publish': True,
                'publish_date': cls.matching_values['publish_date'],
                'order': cls.matching_values['order'],
                'version': cls.matching_values['version'],
                'serial_number': cls.matching_values['serial_number'],
                'tags': cls.matching_values['tags'],
                'top_comment': {}
            }
        ]

        non_matching_articles = []

        for i in range(100):

            # one divergent parameter should exclude the article
            exclude_match = random.choice((
                'text', 'publish', 'publish_date', 'order', 'version',
                'serial_number', 'tags'
            ))

            title = "Non matching article #{}".format(i)

            if exclude_match == 'text':
                text = "Non matching text #{}".format(i)
            else:
                text = cls.matching_values['text']

            if exclude_match == 'publish':
                publish = False
            else:
                publish = True

            if exclude_match == 'publish_date':
                publish_date = datetime(
                    random.randint(1950, 2000),
                    random.randint(1, 12),
                    random.randint(1, 27)
                )
            else:
                publish_date = cls.matching_values['publish_date']

            if exclude_match == 'order':
                order = random.randint(0, 100)
            else:
                order = cls.matching_values['order']

            if exclude_match == 'version':
                version = float('1.{}'.format(random.randint(0, 9)))
            else:
                version = cls.matching_values['version']

            if exclude_match == 'serial_number':
                serial_number = random.randint(
                    1000000000000000000, 2000000000000000000
                )
            else:
                serial_number = cls.matching_values['serial_number']

            if exclude_match == 'tags':
                tags = ['nonmatching_tag1', 'nonmatching_tag2']
            else:
                tags = cls.matching_values['tags']

            non_matching_articles.append({
                'title': title,
                'text': text,
                'publish': publish,
                'publish_date': publish_date,
                'order': order,
                'version': version,
                'serial_number': serial_number,
                'tags': tags,
                'top_comment': {}
            })

        # Load some initial data for this test case
        initial_data = matching_articles + non_matching_articles

        for article in initial_data:
            Article(**article).save()

        params = {}

        for key, value in cls.matching_values.items():
            if key == 'publish_date':
                params[key] = value.isoformat()
            elif key == 'tags':
                params[key] = ','.join(value)
            else:
                params[key] = unicode(value)

        query_string = '?{}'.format(
            '&'.join([
                '{}={}'.format(key, value)
                for key, value in params.items()
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
            for key, value in self.matching_values.items():

                if key == 'publish_date':
                    value = value.isoformat()

                self.assertEqual(article[key], value)
