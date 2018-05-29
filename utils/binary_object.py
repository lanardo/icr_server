import cv2
import base64

MAX_WIDTH = 500


def img2binary(image, tar_width=None):
    h, w = image.shape[:2]
    if tar_width is None:
        tar_width = w

    image = cv2.resize(image, (int(tar_width), int(h * tar_width / w)))
    retval, buffer = cv2.imencode('.jpg', image)
    jpg_as_text = base64.b64encode(buffer)
    base_string = jpg_as_text.decode('utf-8')
    return base_string
