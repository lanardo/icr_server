import re
import io
import os
import cv2
import sys
import copy
import math
import json
import base64
import difflib
import requests
# import skimage.io
import numpy as np
import queue as qu


from PIL import Image, ExifTags
from io import BytesIO
from operator import itemgetter
from fuzzywuzzy import fuzz


ALLOWED_EXT = [".pdf", ".jpg"]

# predefined the location for saving the uploaded files
UPLOAD_DIR = 'data/'

# endpoints
LOG_DIR = "./logs/"
ORIENTATIONS = ["270 Deg", "180 Deg", "90 Deg", "0 Deg(Normal)"]

MACHINE = "EC2"  # which is for the pdf manager

try:
    from utils.settings_local import *
except Exception:
    pass


DST_BUCKET = "icr.json-result"
