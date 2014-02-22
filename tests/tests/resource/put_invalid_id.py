import unittest
import json
from app import server


class ResourcePutInvalidId(unittest.TestCase):
    """
    Test if a HTTP PUT that with an invalid id format gives the right
    response.
    """

    @classmethod
    def setUpClass(cls):

        cls.app = server.app.test_client()

        cls.response = cls.app.put(
            '/articles/{}/'.format('invalid_id_format'),
            headers={'content-type': 'application/json'},
            data=json.dumps({'data': "shouldn't matter"})
        )

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
        Test if the deserialized response data evaluates back to our
        data we posted to the resource in `setUpClass`.
        """

        response_data = json.loads(self.response.data)

        self.assertEqual(
            response_data,
            {'message': (
                "The formatting for the identifier 'invalid_id_format' "
                "is invalid"
            )}
        )
