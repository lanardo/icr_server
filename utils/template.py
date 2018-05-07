import json
import os
import sys


class Template:
    def __init__(self):
        self.dataset = "./dataset/templates"

    def load(self):
        templates_dir = self.dataset
        if not os.path.isdir(templates_dir):
            sys.stdout.write("\tno exist dir: {}\n".format(templates_dir))
            sys.exit(1)

        templates = []
        fnames = [fname for fname in os.listdir(templates_dir) if fname[-5:].lower() == ".json"]
        for fname in fnames:
            json_path = os.path.join(templates_dir, fname)
            str_data = ''
            # read the json file
            if sys.version_info[0] == 3:
                with open(json_path, encoding='utf-8') as f:  # python 3x|
                    str_data = f.read()
            elif sys.version_info[0] == 2:
                with open(json_path, 'r') as f:  # python 2x
                    str_data = f.read()

            # parsing the string data
            if str_data != '':
                try:
                    temp_dict = json.loads(str_data)
                    if temp_dict["type"] == "invoice":
                        templates.append(temp_dict)
                    else:
                        sys.stdout.write("should be invoice: {}\n".format(temp_dict["type"]))
                except Exception as e:
                    print(e)
        return templates
