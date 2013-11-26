import copy
import unittest
import json
from datetime import datetime
from pymongo import MongoClient
from app import server
from app.documents import Article, Comment, Vote


class ResourcePostListFieldMultiple(unittest.TestCase):
    """
    Test if a HTTP POST that adds entries to a listfield on a resource
    gives the right response and adds the data in the database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        cls.initial_data = {
            'title': "Test title",
            'text': "Test text",
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
                    text="Test comment 2 old",
                    email="test2@example.com",
                    upvotes=[
                        Vote(ip_address="1.4.1.4", date=datetime(2013, 5, 2, 9, 1, 3)),
                        Vote(ip_address="2.4.9.2", date=datetime(2013, 8, 2, 8, 2, 1))
                    ]
                ),

            ],
            'top_comment': Comment(
                text="Top comment",
                email="test@example.com",
                upvotes=[
                    Vote(ip_address="5.4.1.2", date=datetime(2012, 5, 2, 9, 2, 3)),
                    Vote(ip_address="2.4.1.2", date=datetime(2012, 3, 2, 8, 2, 1))
                ]
            ),
            'tags': ["tag1", "tag2", "tag3"]
        }

        article = Article(**cls.initial_data).save()

        cls.add_data = [
            {
                'text': "Test comment new",
                'email': "test-new@example.com",
                'upvotes': [
                    { 'ip_address': "1.2.3.4" },
                    { 'ip_address': "2.2.3.4" }
                ]
            },
            {
                'text': "Test comment new 2",
                'email': "test-new-2@example.com",
                'upvotes': [
                    { 'ip_address': "3.2.3.4" },
                    { 'ip_address': "2.2.2.4" }
                ]
            }
        ]

        cls.response = cls.app.post(
            '/articles/{}/comments/'.format(unicode(article['id'])),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.add_data)
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

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        for i, comment in enumerate(response_data):
            response_data[i] = {
                'text': comment['text'],
                'upvotes': [
                    { 'ip_address': comment['upvotes'][0]['ip_address'] },
                    { 'ip_address': comment['upvotes'][1]['ip_address'] }
                ]
            }

        # Remove the `email` field because it's a writeonly field and
        # isn't exposed in the resource.
        original_data = copy.deepcopy(self.add_data)
        for i, comment in enumerate(original_data):
            del(original_data[i]['email'])

        self.assertEqual(response_data, original_data)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the documents, and
        if the initial data is still there.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.initial_data['title'])
        self.assertEqual(article.text, self.initial_data['text'])
        self.assertEqual(article.publish, self.initial_data['publish'])
        self.assertEqual(
            article.publish_date,
            self.initial_data['publish_date']
        )

        # The initial comments should still be present
        self.assertEqual(
            article.comments[0].text,
            self.initial_data['comments'][0]['text']
        )
        self.assertEqual(
            article.comments[0].email,
            self.initial_data['comments'][0]['email']
        )

        self.assertEqual(
            article.comments[1].text,
            self.initial_data['comments'][1]['text']
        )
        self.assertEqual(
            article.comments[1].email,
            self.initial_data['comments'][1]['email']
        )

        # The updated comments should be added
        self.assertEqual(
            article.comments[2].text,
            self.add_data[0]['text']
        )
        self.assertEqual(
            article.comments[2].email,
            self.add_data[0]['email']
        )

        self.assertEqual(
            article.comments[3].text,
            self.add_data[1]['text']
        )
        self.assertEqual(
            article.comments[3].email,
            self.add_data[1]['email']
        )

        self.assertEqual(
            article.top_comment.text,
            self.initial_data['top_comment']['text']
        )
        self.assertEqual(
            article.top_comment.email,
            self.initial_data['top_comment']['email']
        )
        self.assertEqual(
            article.top_comment.upvotes[0].ip_address,
            self.initial_data['top_comment']['upvotes'][0]['ip_address']
        )
        self.assertEqual(
            article.top_comment.upvotes[1].ip_address,
            self.initial_data['top_comment']['upvotes'][1]['ip_address']
        )

        self.assertEqual(
            article.tags,
            self.initial_data['tags']
        )
