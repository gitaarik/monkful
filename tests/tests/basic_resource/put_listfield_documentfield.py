import copy
import unittest
import json
from datetime import datetime
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article, Comment, Vote


class ResourcePutListFieldDocumentField(unittest.TestCase):
    """
    Test if a HTTP PUT that updates a documenfield inside a listfield on
    a resource gives the right response and updates the data in the
    database.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        comment_id = "528a5250aa2649ffd8ce8a90"

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
                    id=comment_id,
                    text="Test comment old 2",
                    email="test2@example.com",
                    upvotes=[
                        Vote(ip_address="1.4.1.4", date=datetime(2013, 5, 2, 9, 1, 3)),
                        Vote(ip_address="2.4.9.2", date=datetime(2013, 8, 2, 8, 2, 1))
                    ]
                ),
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
            'tags': ["tag1", "tag2", "tag3"]
        }

        article = Article(**cls.initial_data).save()

        cls.update_data = {
            'text': "Top comment new",
            'email': "unittest@example.com",
            'upvotes': [
                { 'ip_address': "1.2.3.4" },
                { 'ip_address': "2.2.3.4" }
            ]
        }

        cls.response = cls.app.put(
            '/articles/{}/comments/{}/'.format(
                unicode(article['id']),
                comment_id
            ),
            headers={'content-type': 'application/json'},
            data=json.dumps(cls.update_data)
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

        # Remap the response data so that it only has the fields our
        # orignal data also had.
        response_data = {
            'text': response_data['text'],
            'upvotes': [
                { 'ip_address': response_data['upvotes'][0]['ip_address'] },
                { 'ip_address': response_data['upvotes'][1]['ip_address'] }
            ]
        }

        # Remove the `email` field because it's a writeonly field and
        # isn't exposed in the resource.
        original_data = copy.deepcopy(self.update_data)
        del(original_data['email'])

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
            self.update_data['text']
        )
        self.assertEqual(
            article.comments[1].email,
            self.update_data['email']
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
