import requests
import json
from datetime import datetime
from pprint import pprint


data = {
    'text': 'haho'
}

print 'put data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.put(
    'http://localhost:5000/articles/5282910aaa26493d25a18443/top_comment/',
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
