
import os
import sys
import threading as thr

import cv2

import logger as log
from utils.pre_proc import PreProc
from utils.vision_utils import VisionUtils
from utils.invoice_utils import Invoice
from utils.config import *

if sys.version_info[0] == 3:  # python 3x
    import queue as qu

    try:
        from utils.settings import device
        if device == "EC2":
            from utils.pdf2jpg import Pdf2Jpg
            pdf = Pdf2Jpg()
    except Exception:
        from utils.pdf_utils import PdfUtils
        pdf = PdfUtils()
        pass

elif sys.version_info[0] == 2:  # python 2x
    from utils.pdf2jpg import Pdf2Jpg
    pdf = Pdf2Jpg()
    import Queue as qu


vis = VisionUtils(debug=False)
pre = PreProc(debug=False)
inv = Invoice(debug=True)


def main_proc(src_file, debug=True):

    if not os.path.exists(src_file):
        log.log_print("\t no exist such file! {}\n".format(src_file))
        sys.exit(1)

    # convert pdf to page images ----------------------------------------------------
    log.log_print("\tpdf to imgs...")
    page_img_paths = pdf.doc2imgs(doc_path=src_file)

    # imges to pdf ------------------------------------------------------------------
    log.log_print("\tgoogle vision api...")
    page_contents_queue = qu.Queue()
    threads = []
    while page_contents_queue.qsize() == 0:
        # start the multi requests
        for path in page_img_paths:
            log.log_print("\tpage No: {}".format(page_img_paths.index(path) + 1))
            # detect the text from the image
            idx = page_img_paths.index(path)
            thread = thr.Thread(target=vis.detect_text, args=(path, idx, page_contents_queue))
            threads.append(thread)
            thread.start()
        # join
        for thread in threads:
            if thread is not None and thread.isAlive():
                thread.join()

        if page_contents_queue.qsize() == 0:
            log.log_print("response error. resend the request...")
            break

    # parsing the invoice  -------------------------------------------------------------
    log.log_print("\tpage contents...")
    log.log_print("\t #contents: {}".format(page_contents_queue.qsize()))
    contents = []
    while page_contents_queue.qsize() > 0:
        content = page_contents_queue.get(True, 1)
        if content is None:
            continue

        pre.pre_proc(content)  # preprocessing the page content

        contents.append(content)
        if debug:
            save_temp_images(content=content)

    # parsing and the invoice information -----------------------------------------------------
    if len(contents) == 0:
        log.log_print("\tnot contents\n")
        sys.exit(0)

    log.log_print("\tparse the invoice...")
    contents = sorted(contents, key=lambda k: k['id'])
    res_dict = inv.parse_invoice(contents=contents)
    print(res_dict)
    return res_dict


def save_temp_images(content):
    log.log_print("\t page No     : {}".format(content['id']))
    log.log_print("\t\t page label  : {}".format(content['label']))
    log.log_print("\t\t orientation : {}".format(ORIENTATIONS[content['orientation']]))
    log.log_print("\t\t len of annos: {}".format(len(content['annos'])))
    log.log_print("\t\t image size  : {} x {}".format(content['image'].shape[1], content['image'].shape[0]))
    cv2.imwrite("{}temp_{}.jpg".format(LOG_DIR, content['id'] + 1), content['image'])


if __name__ == '__main__':

    path = "./dataset/samples/InfotechAS/20160408070011.TIF.PDF"
    main_proc(path)
