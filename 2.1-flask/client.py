import requests

responce = requests.post('http://127.0.0.1:5000/user',
                         json={'name': 'user1'},
                         headers={'Auth': 'token'})

# responce = requests.get('http://127.0.0.1:5000/user/1')

# responce = requests.patch('http://127.0.0.1:5000/user/1',
#                           json={'name': 'user10'},
#                           headers={'Auth': 'token'})

print(responce.status_code)
print(responce.text)
print(responce.json())
