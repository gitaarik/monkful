import requests
import json
from random import randint
from datetime import datetime
from pprint import pprint

article_id = '5283b1e2aa2649a692a03415'
comment_id = '5283b1e2aa2649a692a03410'

data = {
    'text': "wajozors! {}".format(randint(0, 100)),
    'date': datetime(2013, 10, 11, 15, 15, 20).isoformat(),
    'email': "testzorzzz@example.com",
}

print 'put data:\n'
pprint(data)

headers = {'content-type': 'application/json; charset=utf-8'}

response = requests.put(
    'http://localhost:5000/articles/{}/comments/{}/'.format(article_id, comment_id),
    data=json.dumps(data),
    headers=headers
)

print '\n{}\n'.format('-' * 100)
print 'reponse:\n'
print 'status code: {}\nbody:\n'.format(response.status_code)
print response.text
