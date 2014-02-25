import requests
import json
from random import randint
from pprint import pprint

article_id = '52839c9aaa26499cfc7e1dc4'

data = {
    'text': 'haho: {}'.format(randint(0, 100))
}

print 'put data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.put(
    'http://localhost:5000/articles/{}/top_comment/'.format(article_id),
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
