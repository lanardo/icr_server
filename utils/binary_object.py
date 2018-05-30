import cv2
import base64

MAX_WIDTH = 500
ENCODING = 'utf-8'


def img2binary(image, tar_width=None):
    h, w = image.shape[:2]
    if tar_width is None:
        tar_width = w

    image = cv2.resize(image, (int(tar_width), int(h * tar_width / w)))
    retval, buffer = cv2.imencode('.jpg', image)
    jpg_as_text = base64.b64encode(buffer)
    base_string = jpg_as_text.decode('utf-8')
    return base_string


def pdf2binary(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        base64_bytes = base64.b64encode(pdf_file.read())

        base64_string = base64_bytes.decode(ENCODING)

        return base64_string
