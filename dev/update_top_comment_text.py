import requests
import json
from pprint import pprint

article_id = '528a5250aa2649ffd8ce8a90'

data = "hoalozors"

print 'put data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.put(
    'http://localhost:5000/articles/{}/top_comment/text/'.format(article_id),
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
