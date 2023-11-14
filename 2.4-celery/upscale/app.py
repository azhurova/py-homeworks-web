from os import getenv

import nanoid
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask.views import MethodView
from flask_pymongo import PyMongo

from celery_app import celery_app, get_task, upscale_photo

load_dotenv()

MONGO_DSN = getenv("MONGO_DSN")

app = Flask("app")

mongo = PyMongo(app, uri=MONGO_DSN)
celery_app.conf.update(app.config)


class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with celery_app.app_context():
            return self.run(*args, **kwargs)


celery_app.Task = ContextTask


class File(MethodView):
    def get(self, file):
        return mongo.send_file(file)


class Upscale(MethodView):
    def get(self, task_id):
        task = get_task(task_id)
        return jsonify({"status": task.status, "result": task.result})

    def post(self):
        image_id = self.save_image("image")
        task = upscale_photo.delay(image_id)
        return jsonify({"task_id": task.id})

    def save_image(self, field) -> str:
        image = request.files.get(field)
        return str(mongo.save_file(f"{nanoid.generate()}{image.filename}", image))


upscale_view = Upscale.as_view("upscale")
file_view = File.as_view("file")

app.add_url_rule("/upscale/", view_func=upscale_view, methods=["POST"])
app.add_url_rule("/tasks/<string:task_id>", view_func=upscale_view, methods=["GET"])
app.add_url_rule("/processed/<string:file>", view_func=file_view, methods=["GET"])
