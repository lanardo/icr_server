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
