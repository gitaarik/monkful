import unittest
import json
from datetime import datetime
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article, Comment, Vote


class ResourcePostListFieldItemListField(unittest.TestCase):
    """
    Test if a HTTP POST that adds entries to a listfield in a item of a
    listfield on a resource gives the right response and adds the data
    in the database.
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
                    id=comment_id,
                    text="Test comment old",
                    email="test@example.com",
                    upvotes=[
                        Vote(
                            ip_address="1.4.1.2",
                            date=datetime(2012, 5, 2, 9, 1, 3),
                            name="Jzorz"
                        ),
                        Vote(
                            ip_address="2.4.5.2",
                            date=datetime(2012, 8, 2, 8, 2, 1),
                            name="Nahnahnah"
                        )
                    ]
                ),
                Comment(
                    text="Test comment 2 old",
                    email="test2@example.com",
                    upvotes=[
                        Vote(
                            ip_address="1.4.1.4",
                            date=datetime(2013, 5, 2, 9, 1, 3),
                            name="Zwefhalala"
                        ),
                        Vote(
                            ip_address="2.4.9.2",
                            date=datetime(2013, 8, 2, 8, 2, 1),
                            name="Jhardikranall"
                        )
                    ]
                ),

            ],
            'top_comment': Comment(
                text="Top comment",
                email="test@example.com",
                upvotes=[
                    Vote(
                        ip_address="5.4.1.2",
                        date=datetime(2012, 5, 2, 9, 2, 3),
                        name="Majananejjeew"
                    ),
                    Vote(
                        ip_address="2.4.1.2",
                        date=datetime(2012, 3, 2, 8, 2, 1),
                        name="Hoeieieie"
                    )
                ]
            ),
            'tags': ["tag1", "tag2", "tag3"]
        }

        article = Article(**cls.initial_data).save()

        cls.add_data = {
            'ip_address': "5.5.5.5",
            'name': "Wejejejeje"
        }

        cls.response = cls.app.post(
            '/articles/{}/comments/{}/upvotes/'.format(
                unicode(article['id']),
                comment_id
            ),
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

        # Remove the date field because it's auto generated and we
        # didn't include it in the original posted data.
        del response_data['date']

        self.assertEqual(response_data, self.add_data)

    def test_documents(self):
        """
        Test if the POST-ed data really ended up in the document
        """
        upvotes = Article.objects[0].comments[0].upvotes
        self.assertEqual(len(upvotes), 3)
        self.assertEqual(upvotes[2].ip_address, self.add_data['ip_address'])
