import requests
import json
from random import randint
from datetime import datetime
from pprint import pprint


data = [
    {
        'text': "wajo {}".format(randint(0, 100)),
        'date': datetime(2013, 10, 11, 15, 15, 20).isoformat(),
        'email': "test@example.com",
    },
    {
        'text': "wajo {}".format(randint(0, 100)),
        'date': datetime(2013, 10, 12, 16, 10, 01).isoformat(),
        'email': "test2@example.com",
    }
]

print 'post data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.post(
    'http://localhost:5000/articles/5282910aaa26493d25a18443/comments/',
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
