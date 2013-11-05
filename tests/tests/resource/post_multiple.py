import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourcePostMultiple(unittest.TestCase):
    """
    Test if a HTTP POST request providing multiple objects gives the
    right response and inserts the data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.data = [
            {
                'title': "Test title",
                'text': "Test text",
                'publish': True,
                'publish_date': datetime(2013, 10, 9, 8, 7, 8).isoformat(),
                'comments': [
                    {
                        'text': "Test comment",

                        # Test if this readonly field will be ignored
                        'date': datetime(2010, 6, 5, 4, 3, 2).isoformat()
                    },
                    {
                        'text': "Test comment 2",

                        # Test if this readonly field will be ignored
                        'date': datetime(2010, 5, 4, 3, 2, 1).isoformat()
                    }
                ],
                'top_comment': {
                    'text': "Top comment"
                },
                'tags': ['test', 'unittest', 'python', 'flask']
            },
            {
                'title': "Test title 2",
                'text': "Test text 2",
                'publish': False,
                'publish_date': datetime(2013, 11, 10, 9, 8, 7).isoformat(),
                'comments': [
                    {
                        'text': "Test comment 3",

                        # Test if this readonly field will be ignored
                        'date': datetime(2010, 4, 3, 2, 1, 2).isoformat()
                    },
                    {
                        'text': "Test comment 4",

                        # Test if this readonly field will be ignored
                        'date': datetime(2010, 3, 2, 1, 2, 3).isoformat()
                    }
                ],
                'top_comment': {
                    'text': "Top comment 2"
                },
                'tags': ['test', 'unittest', 'python', 'flask']
            }
        ]

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
        for i, article in enumerate(response_data):
            for j, comment in enumerate(article['comments']):
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
                        self.data[i]['comments'][j]['date']
                    )

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        for index, article in enumerate(response_data):
            response_data[index] = {
                'title': article['title'],
                'text': article['text'],
                'publish': article['publish'],
                'publish_date': article['publish_date'],
                'comments': [
                    {
                        'text': article['comments'][0]['text']
                    },
                    {
                        'text': article['comments'][1]['text']
                    }
                ],
                'top_comment': {
                    'text': article['top_comment']['text']
                },
                'tags': article['tags']
            }

        # Remove the `date` fields in the `comments` field from the
        # posted data because those will be ignored by the resource
        # because they are readonly fields.
        for article in self.data:
            for comment in article['comments']:
                del(comment['date'])

        self.assertEqual(response_data, self.data)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        i = 0

        for article in Article.objects.all():

            data = self.data[i]
            i += 1

            self.assertEqual(article.title, data['title'])
            self.assertEqual(article.text, data['text'])
            self.assertEqual(
                article.publish_date.isoformat(),
                data['publish_date']
            )
            self.assertEqual(
                article.comments[0].text,
                data['comments'][0]['text']
            )
            self.assertEqual(
                article.comments[1].text,
                data['comments'][1]['text']
            )
            self.assertEqual(
                article.top_comment.text,
                data['top_comment']['text']
            )
            self.assertEqual(
                article.tags,
                data['tags']
            )
