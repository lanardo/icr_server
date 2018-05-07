import logging
import sys
import os

root = os.path.join(os.getcwd(), os.path.dirname(__file__))
LOG_DIR = os.path.join(root, "logs")

if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)
log_fn = LOG_DIR + "/icr.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    datefmt='%d/%b/%Y %H:%M:%S',
                    filename=log_fn)


log_obj = logging


def init():
    if os.path.isfile(log_fn):
        os.remove(log_fn)


def log_print(log_text):
    sys.stdout.write(log_text + "\n")
    if log_text[0] == '\r':
        log_obj.info(log_text[1:])
    else:
        log_obj.info(log_text)
