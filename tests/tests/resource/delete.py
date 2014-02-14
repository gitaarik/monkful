import unittest
from datetime import datetime
from pymongo import MongoClient
from app import server
from app.documents import Article


class ResourceDelete(unittest.TestCase):
    """
    Test if a HTTP DELETE request delets the document and returns the
    right response.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()
        article_id = "528a5250aa2649ffd8ce8a90"

        # Load some initial data for this test case
        cls.data = {
            'articles': [
                {
                    'id': article_id,
                    'title': "Test title",
                    'text': "Test text",
                    'publish': True,
                    'publish_date': datetime(2013, 10, 9, 8, 7, 8),
                    'comments': [
                        {
                            'text': "Test comment",
                            'email': "test@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "1.2.3.4",
                                },
                                {
                                    'ip_address': "2.3.4.5",
                                }
                            ]
                        },
                        {
                            'text': "Test comment 2",
                            'email': "test2@example.com",
                            'upvotes': [
                                {
                                    'ip_address': "3.4.5.6",
                                },
                                {
                                    'ip_address': "4.5.6.7",
                                }
                            ]
                        }
                    ],
                    'top_comment': {
                        'text': "Top comment",
                        'upvotes': [
                            {
                                'ip_address': "5.6.7.8",
                            },
                            {
                                'ip_address': "6.7.8.9",
                            }
                        ]
                    },
                    'tags': ['test', 'unittest', 'python', 'flask']
                }
            ]
        }

        for article in cls.data['articles']:
            Article(**article).save()

        cls.response = cls.app.delete('/articles/{}/'.format(article_id))

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 204.
        """
        self.assertEqual(self.response.status_code, 204)

    def test_content_type(self):
        """
        Test if the content-type header is 'application/json'.
        """
        self.assertEqual(
            self.response.headers['content-type'],
            'application/json'
        )

    def test_empty_response(self):
        """
        If the status code is 204, there should be nothing in the
        response.
        """
        self.assertFalse(self.response.data)

    def test_deleted(self):
        """
        Test if the document is really deleted.
        """
        self.assertEqual(len(Article.objects), 0)
