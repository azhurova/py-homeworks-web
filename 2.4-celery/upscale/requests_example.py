from os import path
import time

import requests

REQUESTS_URL = 'http://127.0.0.1:5000'
EXAMPLE_FILE = 'lama_300px.png'

print('POST request')
resp = requests.post(f'{REQUESTS_URL}/upscale',
                     files={"image": open(path.sep.join([path.dirname(path.realpath(__file__)), EXAMPLE_FILE]), 'rb')})
task_id = resp.json().get("task_id")

status = 'START'
while status not in ['FAILURE', 'SUCCESS']:
    time.sleep(5)
    print(f'GET request {task_id=}')
    resp = requests.get(f'{REQUESTS_URL}/tasks/{task_id}')
    if resp.status_code == 200:
        status = resp.json().get("status")
        print(f'task_status={status}')

        if status == 'SUCCESS':
            filename = resp.json().get("result")
            resp = requests.get(f'{REQUESTS_URL}/processed/{filename}')
            if resp.status_code == 200:
                save_filename = f'upscale_{EXAMPLE_FILE}'
                with open(save_filename, 'wb') as f:
                    f.write(resp.content)
                print(f'Upscaled file save as {save_filename}')
                print('DONE!')
            else:
                print(f'requests_status={resp.status_code}')
                status = 'FAILURE'
    else:
        print(f'requests_status={resp.status_code}')
        status = 'FAILURE'
