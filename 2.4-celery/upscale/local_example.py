import os
from time import sleep

import nanoid
import pymongo
from dotenv import load_dotenv
from gridfs import GridFS

import celery_app

load_dotenv()
MONGO_DSN = os.getenv("MONGO_DSN")


def get_fs():
    mongo = pymongo.MongoClient(MONGO_DSN)
    return GridFS(mongo["files"])


def upscale_my_photo():
    files = get_fs()
    image_path = 'lama_300px.png'
    file_name = f"{nanoid.generate()}{image_path}"
    with open(image_path, 'rb') as f:
        mf = files.new_file(filename=file_name)
        mf.write(f.read())
        file_id = str(mf._id)
        mf.close()

    async_result = celery_app.upscale_photo.delay(file_id)

    status = 'STARTED'
    while status not in ['SUCCESS', 'FAILURE']:
        sleep(1)
        status = celery_app.get_task(async_result.task_id).status
        print(status)

    if status == 'SUCCESS':
        out_file_name = celery_app.get_task(async_result.task_id).result

        with open('lama_600px.png', 'wb') as f:
            image = files.get(out_file_name)
            f.write(image.read())
            image.close()

        print('DONE!')


if __name__ == '__main__':
    upscale_my_photo()
