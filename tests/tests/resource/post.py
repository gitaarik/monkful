import unittest
import json
from pymongo import MongoClient
from app import server
from app.documents import Post


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
            'comments': [
                {
                    'text': "Test comment"
                },
                {
                    'text': "Test comment 2"
                }
            ]
        }

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

        post = Post.objects[0]

        self.assertEqual(post.title, self.data['title'])
        self.assertEqual(post.text, self.data['text'])
        self.assertEqual(
            post.comments[0].text,
            self.data['comments'][0]['text']
        )
        self.assertEqual(
            post.comments[1].text,
            self.data['comments'][1]['text']
        )
