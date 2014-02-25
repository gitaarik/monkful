import requests
import json
from pprint import pprint

article_id = '52862ac2aa2649765afe3bed'
comment_id = '52863220aa2649798726d67b'

data = 'hohoho'

print 'put data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.put(
    'http://localhost:5000/articles/{}/comments/{}/text/'.format(article_id, comment_id),
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
