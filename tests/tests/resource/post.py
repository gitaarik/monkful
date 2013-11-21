import copy
import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourcePost(unittest.TestCase):
    """
    Test if a HTTP POST request gives the right response and inserts the
    data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.data = {
            'title': "Test title",
            'text': "Test text",
            'publish': True,
            'publish_date': datetime(2013, 10, 9, 8, 7, 8).isoformat(),
            'comments': [
                {
                    'text': "Test comment",

                    # Test if this writeonly field will be inserted but
                    # not exposed in the resourse.
                    'email': 'test@example.com',

                    # Test if this readonly field will be ignored on
                    # insertion
                    'date': datetime(2010, 6, 5, 4, 3, 2).isoformat(),
                    'upvotes': [
                        { 'ip_address': "1.2.3.4" },
                        { 'ip_address': "2.2.3.4" }
                    ]
                },
                {
                    'text': "Test comment 2",

                    # Test if this writeonly field will be inserted but
                    # not exposed in the resourse.
                    'email': "test2@example.com",

                    # Test if this readonly field will be ignored on
                    # insertion
                    'date': datetime(2010, 5, 4, 3, 2, 1).isoformat(),
                    'upvotes': [
                        { 'ip_address': "1.3.3.4" },
                        { 'ip_address': "2.4.3.4" }
                    ]
                }
            ],
            'tags': ["test", "unittest", "python", "flask"],
            'top_comment': {
                'text': "Top comment",
                'upvotes': [
                    { 'ip_address': "5.4.1.2"},
                    { 'ip_address': "2.4.1.2"}
                ]
            }
        }

        cls.response = cls.app.post(
            '/articles/',
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.data)
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

        # Check that the readonly field `date` in `comments` is present
        # and is a valid date and is not the date posted because it's a
        # readonly field and should be ignored when supplied in the POST
        # payload.
        for i, comment in enumerate(response_data['comments']):
            try:
                parser.parse(comment['date'])
            except:
                self.fail(
                    "Could not parse the value `{}` into a date object "
                    "in `date` in `comments`."
                    .format(comment['date'])
                )
            else:
                self.assertNotEqual(
                    comment['date'],
                    self.data['comments'][i]['date']
                )

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        response_data = {
            'title': response_data['title'],
            'text': response_data['text'],
            'publish': response_data['publish'],
            'publish_date': response_data['publish_date'],
            'comments': [
                {
                    'text': response_data['comments'][0]['text'],
                    'upvotes': [
                        { 'ip_address': response_data['comments'][0]
                            ['upvotes'][0]['ip_address'] },
                        { 'ip_address': response_data['comments'][0]
                            ['upvotes'][1]['ip_address'] },
                    ]
                },
                {
                    'text': response_data['comments'][1]['text'],
                    'upvotes': [
                        { 'ip_address': response_data['comments'][1]
                            ['upvotes'][0]['ip_address'] },
                        { 'ip_address': response_data['comments'][1]
                            ['upvotes'][1]['ip_address'] },
                    ]
                }
            ],
            'tags': response_data['tags'],
            'top_comment': {
                'text': response_data['top_comment']['text'],
                'upvotes': [
                    { 'ip_address': response_data['top_comment']
                        ['upvotes'][0]['ip_address'] },
                    { 'ip_address': response_data['top_comment']
                        ['upvotes'][1]['ip_address'] },
                ]
            }
        }

        # Remove the `date` fields in the `comments` field from the
        # posted data because those will be ignored by the resource
        # because they are readonly fields.
        # Also remove the `email` field because it's a writeonly field
        # and ins't be exposed in the API.
        original_data = copy.deepcopy(self.data)
        for comment in original_data['comments']:
            del(comment['date'])
            del(comment['email'])

        self.assertEqual(response_data, original_data)

        # Make sure the `email` field in the `comments` field in the
        # response is not present, because it's a writeonly field.
        for comment in response_data:
            self.assertNotIn('email', comment)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.data['title'])
        self.assertEqual(article.text, self.data['text'])
        self.assertEqual(article.publish, self.data['publish'])
        self.assertEqual(
            article.publish_date.isoformat(),
            self.data['publish_date']
        )

        self.assertEqual(
            article.comments[0].text,
            self.data['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[0].email,
            self.data['comments'][0]['email']
        )
        self.assertEqual(
            article.comments[0].upvotes[0].ip_address,
            self.data['comments'][0]['upvotes'][0]['ip_address']
        )

        self.assertEqual(
            article.comments[1].text,
            self.data['comments'][1]['text']
        )
        self.assertEqual(
            article.comments[1].email,
            self.data['comments'][1]['email']
        )
        self.assertEqual(
            article.comments[1].upvotes[0].ip_address,
            self.data['comments'][1]['upvotes'][0]['ip_address']
        )

        self.assertEqual(
            article.tags,
            self.data['tags']
        )
