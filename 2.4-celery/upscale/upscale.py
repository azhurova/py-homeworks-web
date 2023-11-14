from os.path import splitext

import cv2
import numpy
from cv2 import dnn_superres
from gridfs import GridIn, GridOut
from singleton_decorator import singleton


@singleton
class Scaler:
    def __init__(self, model_path):
        self.scaler = dnn_superres.DnnSuperResImpl_create()
        self.scaler.readModel(model_path)
        self.scaler.setModel("edsr", 2)


def upscale(input_image: GridOut, upscale_image: GridIn) -> str:
    """
    :param input_image: изображение для апскейла
    :param upscale_image: файл для сохранения изображения
    :return:
    """
    scaler = Scaler(model_path='EDSR_x2.pb').scaler

    try:
        image_as_np = numpy.frombuffer(input_image.read(), dtype=numpy.uint8)
    finally:
        input_image.close()
    image = cv2.imdecode(image_as_np, cv2.IMREAD_COLOR)

    result_image = scaler.upsample(image)

    file_extension = '.'
    if hasattr(input_image, 'content_type'):
        cnt_type = input_image.content_type.split('/')
        if len(cnt_type) > 1:
            file_extension += input_image.content_type.split('/')[1]
    if len(file_extension) == 1:
        if hasattr(input_image, 'filename'):
            file_extension = splitext(input_image.filename)[1]
    if len(file_extension) == 1:
        file_extension = '.jpeg'

    image_as_bytes = cv2.imencode(file_extension, result_image)[1].tobytes()

    try:
        upscale_image.write(image_as_bytes)
        return upscale_image.filename
    finally:
        upscale_image.close()
