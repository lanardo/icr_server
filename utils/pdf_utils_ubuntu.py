import sys
import os
import cv2
import logger as log


class PdfUtilsUbuntu:

    def __init__(self):
        pass

    def doc2imgs(self, doc_path):
        _, ext = os.path.splitext(os.path.basename(doc_path))
        file_type = ext[1:].lower()

        if file_type in ["pdf"]:
            img_paths = self.pdfTojpgs(pdf_path=doc_path)
        elif file_type in ["png", "jpg"]:
            img_paths = [doc_path]
        else:
            log.log_print("not supported file type.")
            sys.exit(1)
        img_paths.sort()
        return img_paths

    def pdfTojpgs(self, pdf_path):

        if not os.path.isfile(pdf_path):
            log.log_print("\tNo exist such pdf file {}".format(pdf_path))
            sys.exit(1)

        _, ext = os.path.splitext(os.path.basename(pdf_path))
        file_type = ext[1:].upper()

        if file_type in ["PDF"]:
            page_imgs = self.__pdf2imgs_ppm(pdf_path)
            log.log_print("\t pages: # {}".format(len(page_imgs)))
            return page_imgs
        else:  # not yet
            log.log_print("Not defined file type.")
            sys.exit(1)

    def __pdf2imgs_ppm(self, _pdf_path):

        # get the base name for the converted jpg image files
        dir, fname = os.path.split(_pdf_path)
        base, ext = os.path.splitext(fname)
        out_base, _ = os.path.splitext(_pdf_path)

        # convert the pdf file to the jpg images
        command = 'pdftoppm %s %s -jpeg' % (_pdf_path.replace(' ', '\ '), out_base.replace(' ', '\ '))
        os.system(command)

        paths = []
        # convert the jpg files to the list of cv image
        for f in os.listdir(dir):
            path = os.path.join(dir, f)
            if os.path.exists(path) and f.find(base) != -1 and os.path.splitext(f)[1].find('jpg') != -1:
                paths.append(path)

        return paths


if __name__ == '__main__':
    import os, PythonMagick
    from PythonMagick import Image
    from datetime import datetime

    bg_colour = "#ffffff"
    input_pdf = pdf_dir + "\\" + pdf
    img = Image()
    img.density('300')
    img.read(input_pdf)
