import traceback
from os import getenv
from os.path import splitext

import nanoid
import pymongo
from bson.objectid import ObjectId
from cachetools import cached
from celery import Celery, states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from dotenv import load_dotenv
from gridfs import GridFS

from upscale import upscale

load_dotenv()
PG_DSN = getenv("PG_DSN")
CELERY_BROKER = getenv("CELERY_BROKER")
MONGO_DSN = getenv("MONGO_DSN")

celery_app = Celery("app", backend=f"db+{PG_DSN}", broker=CELERY_BROKER, broker_connection_retry_on_startup=True)


def get_task(task_id: str) -> AsyncResult:
    return AsyncResult(task_id, app=celery_app)


@cached({})
def get_fs():
    mongo = pymongo.MongoClient(MONGO_DSN)
    return GridFS(mongo["files"])


@celery_app.task(name='upscale_photo', bind=True)
def upscale_photo(self, image_id):
    try:
        files = get_fs()
        input_image = files.get(ObjectId(image_id))
        kwargs = {}
        if hasattr(input_image, 'content_type'):
            kwargs.update({'content_type': input_image.content_type})
        if hasattr(input_image, 'filename'):
            file_extension = splitext(input_image.filename)[1]
        else:
            file_extension = ''
        kwargs.update({'md5': str(input_image._id)})
        output_image = files.new_file(filename=f"{nanoid.generate(size=24)}{file_extension}", **kwargs)
        try:
            return upscale(input_image, output_image)
        finally:
            files.delete(ObjectId(image_id))
    except Exception as ex:
        self.update_state(state=states.FAILURE,
                          meta={'exc_type': type(ex).__name__, 'exc_message': traceback.format_exc().split('\n'), })
        raise Ignore()
