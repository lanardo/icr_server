import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, send_file
from werkzeug.utils import secure_filename
from collections import OrderedDict

import endpoints
import logger as log
from utils.config import *

"""
*-------------------------------------------------------*
|                   Flask Sever Session                 |
*-------------------------------------------------------*
"""

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXT


@app.route('/submit', methods=['POST'])
def submit():
    if len(request.files) > 0:
        file = request.files['file']
        doc_fn = secure_filename(file.filename)

        if not (file and allowed_file(file.filename)):
            str = "\tnot allowed file format {}.".format(doc_fn)
            log.log_print(str)
            return str
        try:
            # upload the file to the server -------------------------------------------------------
            log.log_print("\tup invoice [{}]".format(file.filename))

            # check its directory for uploading the requested file --------------------------------
            if not os.path.isdir(UPLOAD_DIR):
                os.mkdir(UPLOAD_DIR)

            # remove all the previous processed document file -------------------------------------
            for fname in os.listdir(UPLOAD_DIR):
                path = os.path.join(UPLOAD_DIR, fname)
                if os.path.isfile(path):
                    os.remove(path)

            # save the uploaded document on UPLOAD_DIR --------------------------------------------
            file.save(os.path.join(UPLOAD_DIR, doc_fn))

            # ocr progress with the uploaded files ------------------------------------------------
            log.log_print("\tparse the invoice [{}]".format(doc_fn))
            src_fpath = os.path.join(UPLOAD_DIR, doc_fn)
            invoice_info = endpoints.main_proc(src_file=src_fpath)
            log.log_print("\n--- Finished1 -------------------------------------------------------")
            return jsonify(invoice=OrderedDict(invoice_info))

        except Exception as e:
            str = '\tException: {}'.format(e)
            log.log_print("\t exception :" + str(e))
            return str


if __name__ == '__main__':
    # open the port 5000 to connect betweeen client and server
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
        threaded=True,
    )
