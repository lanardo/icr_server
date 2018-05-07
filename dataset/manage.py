import json
import os
import sys

import cv2

if sys.version_info[0] == 3:  # python 3x
    from utils import PdfUtils
    pdf = PdfUtils()
elif sys.version_info[0] == 2:  # python 2x
    from utils import Pdf2Jpg
    pdf = Pdf2Jpg()


class Manager:
    def __init__(self):
        self.pdf = pdf

    def load_templates(self, json_path):
        if not os.path.isfile(json_path):
            sys.stdout.write("\tno exist json file: {}\n".format(json_path))
            sys.exit(1)

        str_data = ''
        # read the json file
        if sys.version_info[0] == 3:
            with open(json_path, encoding='utf-8') as f:  # python 3x
                str_data = f.read()
        elif sys.version_info[0] == 2:
            with open(json_path, 'r') as f:  # python 2x
                str_data = f.read()

        # parsing the string data
        if str_data != '':
            try:
                temp_dict = json.loads(str_data)
                return temp_dict
            except Exception as e:
                print(e)

    def gen_standard_page_imgs(self, pdf_path):

        page_img_paths = self.pdf.doc2imgs(pdf_path=pdf_path)
        print(pdf_path)
        for path in page_img_paths:
            img = cv2.imread(path)
            img = cv2.resize(img, (1000, 1000))
            cv2.imwrite(path, img)

    # def split(self):
    #     json_path = "../dataset/receipt_dataset.json"
    #
    #     templates = self.load_templates(json_path)
    #     for template in templates:
    #         main_key = template["receipt"]["keywords"][0]
    #
    #         _new = template["receipt"]
    #         _new["type"] = "receipt"
    #
    #         del _new['receipt_id']
    #         _new["sample_fname"] = _new["display_name"]
    #         del _new["display_name"]
    #
    #         template_path = "../dataset/templates/" + main_key + ".json"
    #         with open(template_path, 'w', encoding='utf-8') as f:
    #             json.dump(template, f, ensure_ascii=False, indent=2)

    def validate_dataset(self):
        documents_dir = "../data/documents"
        dataset_dir = "./templates"

        if not os.path.isdir(documents_dir):
            sys.stderr.write("no exist such directory {}.\n".format(documents_dir))
            sys.exit(1)

        if not os.path.isdir(dataset_dir):
            sys.stderr.write("no exist such dataset {}.\n".format(dataset_dir))
            sys.exit(1)

        fnames = os.listdir(dataset_dir)
        fnames.sort()

        for fname in fnames:
            print(fname)
            try:
                template_path = os.path.join(dataset_dir, fname)
                template = self.load_template(template_path)

                doc_path = os.path.join(documents_dir, template['utils']['sample_fname'])
                print(doc_path)
                # convert pdf to document
                pdf.doc2imgs(doc_path=doc_path)
                # load the image
                img = cv2.imread(doc_path[:-4] + "-1.jpg")
                height, width = img.shape[:2]

                sub_parts = template['utils']['parts']['company_info']['sub_parts']

                # company part
                com_rect = sub_parts['company_part']['position']
                rect = [(int(com_rect['x'] * width), int(com_rect['y'] * height)),
                        (int(com_rect['width'] * width), int(com_rect['height'] * height))]
                cv2.rectangle(img, rect[0], (rect[1][0] + rect[0][0], rect[1][1] + rect[0][1]), (255, 0, 0), 2)
                # bill part
                bill_rect = sub_parts['bill_part']['position']
                rect = [(int(bill_rect['x'] * width), int(bill_rect['y'] * height)), (int(bill_rect['width'] * width), int(bill_rect['height'] * height))]
                cv2.rectangle(img, rect[0], (rect[1][0] + rect[0][0], rect[1][1] + rect[0][1]), (0, 255, 0), 2)
                # ship part
                if 'ship_part' in sub_parts.keys():
                    ship_rect = sub_parts['ship_part']['position']
                    rect = [(int(ship_rect['x'] * width), int(ship_rect['y'] * height)), (int(ship_rect['width'] * width), int(ship_rect['height'] * height))]
                    cv2.rectangle(img, rect[0], (rect[1][0] + rect[0][0], rect[1][1] + rect[0][1]), (0, 0, 255), 2)

                cv2.imshow("image", cv2.resize(img, (int(img.shape[1] / 1.5), int(img.shape[1] / 1.5))))
                cv2.waitKey(0)

            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':

    man = Manager()

    # dir_path = "../data/documents"
    # fnames = os.listdir(dir_path)
    # for fname in fnames:
    #     path = os.path.join(dir_path, fname)
    #     dataset.gen_standard_page_imgs(path)

    # print(dataset.load_templates("../dataset/receipt_dataset.json"))

    man.validate_dataset()