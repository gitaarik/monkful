import unittest
import json
from pymongo import MongoClient
from apps.basic_resource import server
from apps.basic_resource.documents import Article


class ResourceGetListPaging(unittest.TestCase):
    """
    Test if the paging on a resource works correctly.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()
        cls.mongo_client = MongoClient()

        for i in range(450):
            article = {
                'title': "title #{}".format(i),
                'top_comment': {}
            }
            Article(**article).save()

        cls.test_cases = {
            'no_page_param': {
                'response': cls.app.get('/articles/'),
                'expected_len': 100,
                'expected_link_header': (
                    '<http://localhost/articles/?page=2>; rel="next", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
            'page_param1': {
                'response': cls.app.get('/articles/?page=1'),
                'expected_len': 100,
                'expected_link_header': (
                    '<http://localhost/articles/?page=2>; rel="next", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
            'page_param2': {
                'response': cls.app.get('/articles/?page=2'),
                'expected_len': 100,
                'expected_link_header': (
                    '<http://localhost/articles/?page=1>; rel="prev", '
                    '<http://localhost/articles/?page=3>; rel="next", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
            'page_param3': {
                'response': cls.app.get('/articles/?page=3'),
                'expected_len': 100,
                'expected_link_header': (
                    '<http://localhost/articles/?page=2>; rel="prev", '
                    '<http://localhost/articles/?page=4>; rel="next", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
            'page_param4': {
                'response': cls.app.get('/articles/?page=4'),
                'expected_len': 100,
                'expected_link_header': (
                    '<http://localhost/articles/?page=3>; rel="prev", '
                    '<http://localhost/articles/?page=5>; rel="next", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
            'page_param5': {
                'response': cls.app.get('/articles/?page=5'),
                'expected_len': 50,
                'expected_link_header': (
                    '<http://localhost/articles/?page=4>; rel="prev", '
                    '<http://localhost/articles/?page=1>; rel="first", '
                    '<http://localhost/articles/?page=5>; rel="last"'
                )
            },
        }

    @classmethod
    def tearDownClass(cls):
        cls.mongo_client.unittest_monkful.article.remove()

    def test_status_code(self):
        """
        Test if the response status code is 200.
        """
        for test_case in self.test_cases.values():
            self.assertEqual(test_case['response'].status_code, 200)

    def test_content_type(self):
        """
        Test if the content-type header is 'application/json'.
        """
        for test_case in self.test_cases.values():
            self.assertEqual(
                test_case['response'].headers['content-type'],
                'application/json'
            )

    def test_json(self):
        """
        Test if the response data is valid JSON.
        """
        for test_case in self.test_cases.values():
            try:
                json.loads(test_case['response'].data)
            except:
                self.fail("Response is not valid JSON.")

    def test_num_docs(self):
        """
        Test if the number of documents in the response in correct.
        """

        for test_case in self.test_cases.values():
            self.assertEqual(
                len(json.loads(test_case['response'].data)),
                test_case['expected_len']
            )

    def test_link_headers(self):
        """
        Test if the `Link` headers in the responses are correct.
        """

        for test_case in self.test_cases.values():
            self.assertEqual(
                test_case['response'].headers['Link'],
                test_case['expected_link_header']
            )
