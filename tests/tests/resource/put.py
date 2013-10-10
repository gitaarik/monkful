import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Article, Comment


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
            'published': True,
            'comments': [
                Comment(text="Test comment old"),
                Comment(text="Test comment old 2"),

                # Test to see if this third comment gets removed on
                # update
                Comment(text="Test comment old 3"),
            ],
            'top_comment': Comment(text="Top comment old")
        }

        cls.data_new = {
            'title': "Test title new",
            'text': "Test text new",
            'published': False,
            'comments': [
                { 'text': "Test comment new" },
                { 'text': "Test comment new 2" }
            ],
            'top_comment': {
                'text': "Top comment new"
            }
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
            self.fail("Respnose is not valid JSON.")

    def test_content(self):
        """
        Test if the deserialized response data evaluates back to our
        data we posted to the resource in `setUpClass`.
        """

        response_data = json.loads(self.response.data)
        response_data = {
            'title': response_data['title'],
            'text': response_data['text'],
            'published': response_data['published'],
            'comments': [
                {
                    'text': response_data['comments'][0]['text']
                },
                {
                    'text': response_data['comments'][1]['text']
                }
            ],
            'top_comment': {
                'text': response_data['top_comment']['text']
            }
        }

        self.assertEqual(response_data, self.data_new)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.data_new['title'])
        self.assertEqual(article.text, self.data_new['text'])
        self.assertEqual(
            article.comments[0].text,
            self.data_new['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[1].text,
            self.data_new['comments'][1]['text']
        )

        # The complete `comments` field should've been overwritten so
        # there should be only two comments instead of 3.
        self.assertEqual(len(article.comments), 2)
