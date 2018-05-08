import sys
import base64
import cv2
import copy
import utils.text_annos_manage as manager
from utils.template import Template
from utils.string_manage import *
import logger as log


EMP = ""
THRESH_MIN_LINE_KEYS = 3


class Invoice:
    def __init__(self, debug, show_img_w=300):
        self.debug = debug
        self.show_img_w = show_img_w
        self.show_line_w = 2

        self.templates = Template().load()

    def recognize_template_id(self, content):
        total_text = content['total_text']
        texts = total_text.split("\n")

        template = None
        for temp in self.templates:
            for text in texts:
                for keyword in temp['prefix']["keywords"]:
                    if text.replace(' ', '').find(keyword.replace(' ', '')) != -1:
                        template = temp
                if template is not None:
                    break
            if template is not None:
                break
        return template

    def get_details_infos(self, template, contents):
        content = contents[0]  # get details info from the first page
        annos = content['annos']
        lines = content['lines']
        infos = template['info']['InvoiceDetails']
        ret_dict = {}

        for line_id in range(len(lines)):
            line = lines[line_id]
            line_text = ""
            for anno_id in line['line']:
                line_text += annos[anno_id]['text']

            for info in infos:
                for keyword in info['keywords']:
                    if keyword == EMP:
                        ret_dict[info['meaning']] = EMP
                        break

                    pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                    if pos != -1 and info['meaning'] not in ret_dict.keys():
                        value = manager.get_val(annos=annos, keyword=keyword,
                                                lines=lines, line_id=line_id,
                                                info=info)

                        print(info['meaning'], ":", value)
                        ret_dict[info['meaning']] = value
                        if value != EMP:
                            break

        return ret_dict

    def get_line_infos(self, template, contents):
        total_value_lines = []
        for content in contents:
            annos = content['annos']
            lines = content['lines']
            infos = template['info']['InvoiceLines']['components']

            # determine the postion keywords line ---------------------------------
            main_keyword_list = []
            key_line_pos = -1
            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = ""
                for anno_id in line['line']:
                    line_text += annos[anno_id]['text']
                line_text = line_text.replace(' ', '')

                key_list = []
                find_pos = -1
                for info in infos:
                    for keyword in info['keywords']:
                        _key = keyword.replace(' ', '')
                        if _key == EMP: continue
                        find_pos = line_text.find(_key, max(0, find_pos))
                        if find_pos != -1:
                            key_list.append(keyword)
                            break
                        else:
                            _key = EMP
                    find_pos += len(_key)

                if len(key_list) > THRESH_MIN_LINE_KEYS and len(key_list) > len(main_keyword_list):
                    main_keyword_list = copy.deepcopy(key_list)
                    key_line_pos = line_id

            # rearrange the key line based its keywords -------------------------------
            main_keyanno_list = []
            if key_line_pos != -1:
                key_line = lines[key_line_pos]['line']
                i = 0
                k = 0
                start = 0
                while i < len(key_line):
                    temp_str = ""
                    for j in range(start, len(key_line)):
                        anno_text = annos[key_line[j]]['text']
                        temp_str += anno_text
                        end = j
                        if temp_str.replace(' ', '').find(main_keyword_list[k].replace(' ', '')) != -1:
                            main_keyanno_list.append({
                                'keyword': main_keyword_list[k],
                                'left': manager.get_left_edge(annos[key_line[start]]),
                                'right': manager.get_left_edge(annos[key_line[end]])
                            })
                            k += 1
                            start = end + 1
                            break
                    i += 1

            # config the lines ---------------------------------------------------
            if len(main_keyanno_list) != -1:
                value_lines = []
                cnt = 0
                while cnt < 3:
                    for line_id in range(key_line_pos + cnt + 1, len(lines)):
                        line = lines[line_id]['line']

                        value_line = []
                        start = 0
                        for k in range(0, len(main_keyanno_list)):
                            temp_str = EMP
                            if k == 0:
                                for i in range(start, len(line)):
                                    if manager.get_right_edge(annos[line[i]])[0] <= main_keyanno_list[k+1]['left'][0]:
                                        temp_str += annos[line[i]]['text']
                                    else:
                                        start = i
                                        value_line.append(temp_str)
                                        break
                            elif k != len(main_keyanno_list) - 1:
                                for i in range(start, len(line)):
                                    if main_keyanno_list[k - 1]['right'][0] <= manager.get_left_edge(annos[line[i]])[0] and \
                                                    manager.get_right_edge(annos[line[i]])[0] < \
                                                    main_keyanno_list[k + 1]['left'][0]:
                                        temp_str += annos[line[i]]['text']
                                    else:
                                        start = i
                                        value_line.append(temp_str)
                                        break
                            elif k == len(main_keyanno_list) - 1:
                                for i in range(start, len(line)):
                                    if main_keyanno_list[k-1]['right'][0] < manager.get_left_edge(annos[line[i]])[0]:
                                        temp_str += annos[line[i]]['text']
                                value_line.append(temp_str)

                        num_emptys = value_line.count(EMP)
                        if len(value_line) - num_emptys < THRESH_MIN_LINE_KEYS:
                            cnt += 1
                            break
                        if lines[line_id]['pos'] - lines[line_id - 1]['pos'] > manager.get_height(
                                anno=annos[lines[key_line_pos]['line'][0]]) * 3:
                            cnt += 3
                            break
                        else:
                            cnt += 3
                            # init the empty contrainer for result dict
                            filled_list = [EMP] * len(infos)
                            for i in range(len(infos)):
                                info = infos[i]
                                for k in range(len(main_keyanno_list)):
                                    key_anno = main_keyanno_list[k]
                                    if key_anno['keyword'] in info['keywords']:
                                        filled_list[i] = value_line[k]
                                        break

                            # fillout the empty elements
                            value_lines.append(filled_list)

            total_value_lines.extend(value_lines)
        return total_value_lines

    def get_total_infos(self, template, contents):
        content = contents[-1]  # get total info from the last page
        annos = content['annos']
        lines = content['lines']
        totals = template['info']['Totals']
        ret_dict = {}

        if totals['type'] == "list":
            infos = totals['components']
            orientation = totals['orientation']
            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = ""
                for anno_id in line['line']:
                    line_text += annos[anno_id]['text']

                for info in infos:
                    for keyword in info['keywords']:
                        if keyword == EMP:
                            ret_dict[info['meaning']] = EMP
                            break

                        info['orientation'] = orientation
                        pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                        if pos != -1 and info['meaning'] not in ret_dict.keys():
                            last_pos = pos + len(keyword.replace(' ', ''))
                            value = manager.get_val(annos=annos, anno_id=anno_id,
                                                    lines=lines, line_id=line_id,
                                                    cur_val_text=line_text[last_pos:],
                                                    info=info)

                            keyword = info['meaning']
                            ret_dict[keyword] = value
                            if value != EMP:
                                break

            return ret_dict

    def get_tax_infos(self, template, contents):
        content = contents[-1]  # get total info from the last page
        annos = content['annos']
        lines = content['lines']
        taxs = template['info']['TotalTAXs']
        ret_dict = {}

        if taxs['type'] == "list":
            infos = taxs['components']
            orientation = taxs['orientation']

            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = ""
                for anno_id in line['line']:
                    line_text += annos[anno_id]['text']

                for info in infos:
                    for keyword in info['keywords']:
                        if keyword == EMP:
                            ret_dict[info['meaning']] = EMP
                            break

                        info['orientation'] = orientation
                        pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                        if pos != -1 and info['meaning'] not in ret_dict.keys():
                            last_pos = pos + len(keyword.replace(' ', ''))
                            value = manager.get_val(annos=annos, anno_id=anno_id,
                                                    lines=lines, line_id=line_id,
                                                    cur_val_text=line_text[last_pos:],
                                                    info=info)

                            keyword = info['meaning']
                            ret_dict[keyword] = value
                            if value != EMP:
                                break

            return ret_dict

    def parse_invoice(self, contents):
        # recognize the template type -----------------------------------------
        log.log_print("\t recognize the document type")
        template = self.recognize_template_id(content=contents[0])

        if template is None:  # unknown document type
            log.log_print("\tunknown document type.\n")
            return {'error': "unknown document type."}
        else:
            log.log_print("\t\ttemplate: {}.\n".format(template['prefix']['name']))
            invoice_details = self.get_details_infos(template=template, contents=contents)
            invoice_tax = self.get_tax_infos(template=template, contents=contents)
            invoice_total = self.get_total_infos(template=template, contents=contents)
            invoice_lines = self.get_line_infos(template=template, contents=contents)
            return {
                'company': template['prefix']['name'],
                'invoice_details': invoice_details,
                'invoice_lines': invoice_lines,
                'invoice_tax': invoice_tax,
                'invoice_total': invoice_total
            }
