import copy
import unittest
import json
from datetime import datetime
from dateutil import parser
from pymongo import MongoClient
from app import server
from app.documents import Article, Comment, Vote


class ResourcePut(unittest.TestCase):
    """
    Test if a HTTP PUT that updates a resource gives the right response
    and updates the data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.data_old = {
            'title': "Test title old",
            'text': "Test text old",
            'publish': True,
            'publish_date': datetime(2013, 10, 9, 8, 7, 8),
            'comments': [

                Comment(
                    text="Test comment old",
                    email="test@example.com",
                    upvotes=[
                        Vote(ip_address="1.4.1.2", date=datetime(2012, 5, 2, 9, 1, 3)),
                        Vote(ip_address="2.4.5.2", date=datetime(2012, 8, 2, 8, 2, 1))
                    ]
                ),
                Comment(
                    text="Test comment old 2",
                    email="test2@example.com",
                    upvotes=[
                        Vote(ip_address="1.4.1.4", date=datetime(2013, 5, 2, 9, 1, 3)),
                        Vote(ip_address="2.4.9.2", date=datetime(2013, 8, 2, 8, 2, 1))
                    ]
                ),

                # Test to see if this third comment gets removed on
                # update.
                Comment(
                    text="Test comment old 3",
                    email="test3@example.com",
                    upvotes=[
                        Vote(ip_address="5.4.1.2", date=datetime(2012, 5, 2, 9, 2, 3)),
                        Vote(ip_address="2.4.1.2", date=datetime(2012, 3, 2, 8, 2, 1))
                    ]
                ),

            ],
            'top_comment': Comment(
                text="Top comment old",
                email="test@example.com",
                upvotes=[
                    Vote(ip_address="5.4.1.2", date=datetime(2012, 5, 2, 9, 2, 3)),
                    Vote(ip_address="2.4.1.2", date=datetime(2012, 3, 2, 8, 2, 1))
                ]
            ),
            'tags': ["tag1 old", "tag2 old", "tag3 old"]
        }

        cls.data_new = {
            'title': "Test title new",
            'text': "Test text new",
            'publish': False,
            'publish_date': datetime(2013, 11, 10, 9, 8, 7).isoformat(),
            'comments': [
                {
                    'text': "Test comment new",

                    # Test if this readonly field will be ignored
                    'date': datetime(2010, 6, 5, 4, 3, 2).isoformat(),

                    # Test if this writeonly field will be updated
                    'email': "test_updated@example.com",

                    'upvotes': [
                        { 'ip_address': '3.3.3.3' },
                        { 'ip_address': '4.4.4.4' }
                    ]
                },
                {
                    'text': "Test comment new 2",

                    # Test if this readonly field will be ignored
                    'date': datetime(2010, 5, 4, 3, 2, 1).isoformat(),

                    # Test if this writeonly field will be updated
                    'email': "test2_updated@example.com",

                    'upvotes': [
                        { 'ip_address': '5.5.5.5' },
                        { 'ip_address': '6.6.6.6' }
                    ]
                }
            ],
            'top_comment': {
                'text': "Top comment new",
                'email': "test_updated@example.com",
                'date': datetime(2011, 5, 7, 1, 3, 1).isoformat(),
                'upvotes': [
                    { 'ip_address': "1.2.3.4" },
                    { 'ip_address': "2.2.3.4" }
                ]
            },
            'tags': ["tag1 new", "tag2 new", "tag3 new"],
        }

        article = Article(**cls.data_old).save()

        cls.response = cls.app.put(
            '/articles/{}/'.format(unicode(article['id'])),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.data_new)
        )

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
        data we posted to the resource in `setUpClass`.
        """

        response_data = json.loads(self.response.data)

        # Check that the readonly field `date` in `comments` is present
        # and is a valid date and is not the date posted because it's a
        # readonly field and should be ignored when supplied in the PUT
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
                    self.data_new['comments'][i]['date']
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
            'top_comment': {
                'text': response_data['top_comment']['text'],
                'upvotes': [
                    { 'ip_address': response_data['top_comment']
                        ['upvotes'][0]['ip_address'] },
                    { 'ip_address': response_data['top_comment']
                        ['upvotes'][1]['ip_address'] },
                ]
            },
            'tags': response_data['tags']
        }

        # Remove the `date` fields in the `comments` field from the
        # putted data because those will be ignored by the resource
        # because they are readonly fields.
        # Also remove the `email` field because it's a writeonly field
        # and ins't be exposed in the API.
        original_data = copy.deepcopy(self.data_new)
        for comment in original_data['comments']:
            del(comment['date'])
            del(comment['email'])

        del(original_data['top_comment']['date'])
        del(original_data['top_comment']['email'])

        self.assertEqual(response_data, original_data)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.data_new['title'])
        self.assertEqual(article.text, self.data_new['text'])
        self.assertEqual(article.publish, self.data_new['publish'])
        self.assertEqual(
            article.publish_date.isoformat(),
            self.data_new['publish_date']
        )
        self.assertEqual(
            article.comments[0].text,
            self.data_new['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[0].email,
            self.data_new['comments'][0]['email']
        )
        self.assertEqual(
            article.comments[1].text,
            self.data_new['comments'][1]['text']
        )
        self.assertEqual(
            article.comments[1].email,
            self.data_new['comments'][1]['email']
        )

        self.assertEqual(
            article.top_comment.text,
            self.data_new['top_comment']['text']
        )
        self.assertEqual(
            article.top_comment.email,
            self.data_new['top_comment']['email']
        )

        # The complete `comments` field should've been overwritten so
        # there should be only two comments instead of 3.
        self.assertEqual(len(article.comments), 2)

        self.assertEqual(
            article.tags,
            self.data_new['tags']
        )
