from wand.image import Image as WandImage
from wand.color import Color as WandColor
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger

from io import BytesIO
import skimage.io
from PIL import Image
import io

from utils.settings import *
import logger as log


class PdfUtilsWin:

    def __init__(self, resolution=200):
        self.resolution = resolution  # DPI

    def doc2imgs(self, doc_path):
        _, ext = os.path.splitext(os.path.basename(doc_path))
        file_type = ext[1:].lower()

        if file_type in ["pdf"]:
            img_paths = self.pdfTojpgs(pdf_path=doc_path)
        elif file_type in ["png", "jpg"]:
            img_paths = [doc_path]
        else:
            log.log_print("not supported document type.")
            sys.exit(1)
        img_paths.sort()
        return img_paths

    def pdfTojpgs(self, pdf_path):

        if not os.path.exists(pdf_path):
            log.log_print("\tNo exist such pdf file {}".format(pdf_path))
            sys.exit(1)

        trail, fname = os.path.split(pdf_path)
        base, ext = os.path.splitext(fname)
        file_type = ext[1:].upper()
        if file_type in ["PDF"]:  # pdf
            page_imgs = self.__pdf2imgs_wand(pdf_path)
            paths = []
            for id in range(len(page_imgs)):
                img = page_imgs[id]
                img_path = os.path.join(trail, (base + "-" + str(id + 1) + ".jpg"))
                if img is None and os.path.exists(img_path):
                    pass
                else:
                    cv2.imwrite(img_path, img)
                paths.append(img_path)

            log.log_print("\t pages: # {}".format(len(paths)))
            return paths

        else:  # not yet
            log.log_print("\tNot defined file type.")

    def __pdf2imgs_wand(self, _pdf_path):
        # pages of pdf to images
        images = []

        reader = PdfFileReader(open(_pdf_path, "rb"))

        for page_num in range(reader.getNumPages()):
            # read the page of pdf file
            src_page = reader.getPage(page_num)

            # convert src_page to wand image with using PdfFileWriter(dst_page)
            dst_pdf = PdfFileWriter()
            dst_pdf.addPage(src_page)

            pdf_bytes = io.BytesIO()
            dst_pdf.write(pdf_bytes)
            pdf_bytes.seek(0)

            with WandImage(file=pdf_bytes, resolution=self.resolution) as wand_img:
                # convert wand image to ndarray cv
                wand_img.background_color = WandColor('white')
                wand_img.format = 'bmp'
                wand_img.alpha_channel = False
                img_buffer = np.asarray(bytearray(wand_img.make_blob()), dtype=np.uint8)

            if img_buffer is not None:
                bytesio = BytesIO(img_buffer)
                sk_img = skimage.io.imread(bytesio)
                print(sk_img.shape)
                cv_img = sk_img.copy()

            images.append(cv_img)

        return images


if __name__ == '__main__':
    pass
