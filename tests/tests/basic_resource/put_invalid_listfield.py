import copy
import unittest
import json
from datetime import datetime
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article, Comment, Vote


class ResourcePutListField(unittest.TestCase):
    """
    Test if a HTTP PUT that updates a listfield on a resource gives the
    right response.
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

                # Test to see if this third comment gets removed on
                # update.
                Comment(
                    text="Test comment 3 old",
                    email="test3@example.com",
                    upvotes=[
                        Vote(ip_address="5.4.1.2", date=datetime(2012, 5, 2, 9, 2, 3)),
                        Vote(ip_address="2.4.1.2", date=datetime(2012, 3, 2, 8, 2, 1))
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

        cls.update_data = [
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

        cls.response = cls.app.put(
            '/articles/{}/comments/'.format(unicode(article['id'])),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.update_data)
        )

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 400.
        """
        self.assertEqual(self.response.status_code, 400)

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
        Test if the response contains the correct error message.
        """
        response_data = json.loads(self.response.data)
        self.assertEqual(response_data, { 'message': "No id provided" })

    def test_documents(self):
        """
        Test if the POST-ed data didn't end up in the documents, and if
        the initial data is still there.
        """

        article = Article.objects[0]

        self.assertEqual(article.title, self.initial_data['title'])
        self.assertEqual(article.text, self.initial_data['text'])
        self.assertEqual(article.publish, self.initial_data['publish'])
        self.assertEqual(
            article.publish_date,
            self.initial_data['publish_date']
        )

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
        self.assertEqual(
            article.comments[2].text,
            self.initial_data['comments'][2]['text']
        )
        self.assertEqual(
            article.comments[2].email,
            self.initial_data['comments'][2]['email']
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
