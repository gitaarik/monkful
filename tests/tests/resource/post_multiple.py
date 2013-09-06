import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


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
                'published': True,
                'comments': [
                    {
                        'text': "Test comment"
                    },
                    {
                        'text': "Test comment 2"
                    }
                ]
            },
            {
                'title': "Test title 2",
                'text': "Test text 2",
                'published': False,
                'comments': [
                    {
                        'text': "Test comment 3"
                    },
                    {
                        'text': "Test comment 4"
                    }
                ]
            }
        ]

        cls.response = cls.app.post('/posts/', data=json.dumps(cls.data))

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.post.remove()

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
            self.fail("Respnose is not valid JSON.")

    def test_content(self):
        """
        Test if the deserialized response data evaluates back to our
        data we posted to the resource in `setUpClass`.
        """
        self.assertEqual(
            json.loads(self.response.data),
            self.data
        )

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents.
        """

        i = 0

        for post in Post.objects.all():

            data = self.data[i]
            i += 1

            self.assertEqual(post.title, data['title'])
            self.assertEqual(post.text, data['text'])
            self.assertEqual(
                post.comments[0].text,
                data['comments'][0]['text']
            )
            self.assertEqual(
                post.comments[1].text,
                data['comments'][1]['text']
            )
