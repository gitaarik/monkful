import requests
import json
from datetime import datetime
from pprint import pprint


data = {
    'title': "hoho",
    'text': "hellooooo",
    'comments': [
        {
            'text': "hello",
            'date': datetime(2013, 10, 11, 15, 15, 20).isoformat(),
            'email': "test@example.com",
        },
        {
            'text': "hello 2",
            'date': datetime(2013, 10, 12, 16, 10, 01).isoformat(),
            'email': "test2@example.com",
        }
    ],
    'top_comment': {
        'text': "hello",
        'date': datetime(2013, 10, 11, 15, 15, 20).isoformat(),
        'email': "test@example.com",
    },
    'publish': True,
    'publish_date': datetime(2013, 10, 10, 10, 30, 24).isoformat()
}

print 'POST data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.post(
    'http://127.0.0.1:5000/articles/',
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
