import sys
import base64
import copy
import utils.text_annos_manage as manager
from utils.template import Template
import logger as log
import cv2
import re


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
        components = template['info']['InvoiceDetails']
        ret_dict = {}

        for line_id in range(len(lines)):
            line = lines[line_id]
            line_text = ""
            for anno_id in line['line']:
                line_text += annos[anno_id]['text']

            for component in components:
                for keyword in component['keywords']:
                    if keyword == EMP:
                        ret_dict[component['meaning']] = EMP
                        break

                    pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                    if pos != -1 and (component['meaning'] not in ret_dict.keys() or ret_dict[component['meaning']] == EMP):
                        value = manager.get_val(annos=annos, keyword=keyword,
                                                lines=lines, line_id=line_id,
                                                info=component)
                        ret_dict[component['meaning']] = value

        return ret_dict

    def get_line_infos(self, template, contents):
        total_value_lines = []
        for content in contents:
            annos = content['annos']
            lines = copy.deepcopy(content['lines'])
            components = template['info']['InvoiceLines']['components']

            # --- determine the postion keywords line ---------------------------------
            main_keyword_list = []
            key_line_pos = -1
            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = line['text'].replace(' ', '')

                key_list = []
                find_pos = -1
                for component in components:
                    for keyword in component['keywords']:
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

            # --- rearrange the key line based its keywords -------------------------------
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
                                'right': manager.get_right_edge(annos[key_line[end]])
                            })
                            k += 1
                            start = end + 1
                            break
                    i += 1

            # --- index of the "Description" item on the invoiceline components ------
            description_id = -1
            if len(main_keyanno_list) != -1:
                description_keywords = []
                for component in components:
                    if component['meaning'] == "Description":
                        description_keywords = component['keywords']
                for k in range(len(main_keyanno_list)):
                    key_anno = main_keyanno_list[k]
                    if key_anno['keyword'] in description_keywords:
                        description_id = k
                        break

                img = content['image']
                for key_anno in main_keyanno_list:
                    pt1 = key_anno['left']
                    pt2 = key_anno['right']
                    cv2.line(img, (int(pt1[0]), int(pt1[1])), (int(pt2[0]),int(pt2[1])), (0, 255, 255), 10)
                cv2.imwrite("line_1.jpg", img)

            # --- filter the wrong parsed line from the lines
            filtered_lines = []
            if key_line_pos != -1:
                line_id = key_line_pos
                while line_id < len(lines):
                    cur_line = lines[line_id]
                    if len(filtered_lines) == 0:
                        prev_line = lines[line_id - 1]
                        dis = 0.0
                    else:
                        prev_line = filtered_lines[-1]
                        dis = cur_line['pos'] - prev_line['pos']

                    if not manager.is_candi_line(cur_line['text']):
                        line_id += 1
                        continue

                    if dis < manager.get_height(annos[lines[key_line_pos]['line'][0]]):
                        if cur_line['text'].replace(' ', '').find(prev_line['text'].replace(' ', '')) != -1:
                            del filtered_lines[-1]
                            continue
                        elif prev_line['text'].replace(' ', '').find(cur_line['text'].replace(' ', '')) != -1:
                            line_id += 1
                            continue
                    if dis > manager.get_height(annos[lines[key_line_pos]['line'][0]]) * 3:
                        break
                    filtered_lines.append(cur_line)
                    line_id += 1

                # in filtered lines, the keyword_line is the first line
                key_line_pos = 0
                lines = filtered_lines
            # --- config the lines ---------------------------------------------------
            value_lines = []
            if len(main_keyanno_list) != -1:
                for line_id in range(key_line_pos + 1, len(lines)):
                    line = lines[line_id]['line']

                    value_line = []
                    start = 0
                    for k in range(0, len(main_keyanno_list)):
                        temp_str = EMP
                        if k == 0:
                            for i in range(start, len(line)):
                                if manager.get_right_edge(annos[line[i]])[0] <= main_keyanno_list[k+1]['left'][0]:
                                    temp_str += annos[line[i]]['text'] + ' '
                                else:
                                    start = i
                                    value_line.append(temp_str)
                                    break
                        elif k != len(main_keyanno_list) - 1:
                            for i in range(start, len(line)):
                                if main_keyanno_list[k - 1]['right'][0] <= manager.get_left_edge(annos[line[i]])[0] and \
                                                manager.get_right_edge(annos[line[i]])[0] < main_keyanno_list[k + 1]['left'][0]:
                                    if i != len(line) - 1 and manager.distance_anno2anno(left=annos[line[i]], right=annos[line[i + 1]]) < 3 * manager.get_height(annos[lines[key_line_pos]['line'][0]]):
                                        temp_str += annos[line[i]]['text'] + ' '
                                    else:
                                        temp_str += annos[line[i]]['text'] + ' '
                                        value_line.append(temp_str)
                                        start = i + 1
                                        break
                                else:
                                    start = i
                                    value_line.append(temp_str)
                                    break
                        elif k == len(main_keyanno_list) - 1:
                            for i in range(start, len(line)):
                                if main_keyanno_list[k-1]['right'][0] < manager.get_left_edge(annos[line[i]])[0]:
                                    temp_str += annos[line[i]]['text'] + ' '
                            value_line.append(temp_str)

                    num_emptys = value_line.count(EMP)
                    if len(value_line) - num_emptys > THRESH_MIN_LINE_KEYS:
                        value_lines.append(value_line)
                    else:
                        if num_emptys == len(value_line) - 1 and value_line[description_id] != EMP and \
                                        len(value_lines) > 0 and value_lines[-1][description_id] != EMP:
                            value_lines[-1][description_id] += value_line[description_id]
                            continue
                        elif lines[line_id]['pos'] - lines[key_line_pos]['pos'] < manager.get_height(anno=annos[lines[key_line_pos]['line'][0]]) * 3:
                            continue
                        else:
                            break

            # --- fillout the value line with order of components
            if len(value_lines) != -1:
                filled_lines = []
                for value_line in value_lines:
                    # init the empty contrainer for result dict
                    filled_list = [EMP] * len(components)
                    filled_list[0] = str(value_lines.index(value_line))

                    for i in range(len(components)):
                        component = components[i]
                        for k in range(len(main_keyanno_list)):
                            key_anno = main_keyanno_list[k]
                            if key_anno['keyword'] in component['keywords']:
                                filled_list[i] = value_line[k]
                                break
                    filled_lines.append(filled_list)

                total_value_lines.extend(filled_lines)

        return total_value_lines

    def get_total_infos(self, template, contents):
        totals = template['info']['Totals']
        components = totals['components']
        orientation = totals['orientation']

        ret_dict = {}
        for content in contents: # get total info from the last page
            annos = content['annos']
            lines = content['lines']
            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = line['text']

                for component in components:
                    for keyword in component['keywords']:
                        if keyword == EMP:
                            ret_dict[component['meaning']] = EMP
                            break

                        component['orientation'] = orientation
                        pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                        if pos != -1 and (component['meaning'] not in ret_dict.keys() or ret_dict[component['meaning']] == EMP):
                            value = manager.get_val(annos=annos, keyword=keyword,
                                                    lines=lines, line_id=line_id,
                                                    info=component)

                            ret_dict[component['meaning']] = value
                            # if value != EMP:
                            #     print(component['meaning'], ":", value)
                            #     break

        if totals['type'] == "list":
            return ret_dict
        else:
            return ret_dict

    def get_tax_infos(self, template, contents):
        ret_dict = {}

        taxs = template['info']['TotalTAXs']
        components = taxs['components']
        orientation = taxs['orientation']
        for content in contents:
            annos = content['annos']
            lines = content['lines']

            for line_id in range(len(lines)):
                line = lines[line_id]
                line_text = line['text']

                for component in components:
                    for keyword in component['keywords']:
                        if keyword == EMP:
                            ret_dict[component['meaning']] = EMP
                            break

                        component['orientation'] = orientation
                        pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                        if pos != -1 and (component['meaning'] not in ret_dict.keys() or ret_dict[component['meaning']] == EMP):
                            value = manager.get_val(annos=annos, keyword=keyword,
                                                    lines=lines, line_id=line_id,
                                                        info=component)

                            ret_dict[component['meaning']] = value
                            # if value != EMP:
                            #     print(component['meaning'], ":", value)
                            #     break

        if taxs['type'] == "list":
            return ret_dict
        elif taxs['type'] == "dict" and taxs['orientation'] == "under":
            return ret_dict

    def parse_invoice(self, contents):
        # recognize the template type -----------------------------------------
        log.log_print("\t recognize the company...")
        template = self.recognize_template_id(content=contents[0])

        if template is None:  # unknown document type
            log.log_print("\tunknown company document.\n")
            return {'error': "unknown company docuemnt."}
        else:
            log.log_print("\t\ttemplate: {}.\n".format(template['prefix']['name']))
            invoice_details = self.get_details_infos(template=template, contents=contents)
            invoice_tax = self.get_tax_infos(template=template, contents=contents)
            invoice_total = self.get_total_infos(template=template, contents=contents)
            invoice_lines = self.get_line_infos(template=template, contents=contents)

            if self.debug and True:
                print(">>> company:")
                print(template['prefix']['name'])

                print(">>> invoice_details:")
                for key in invoice_details.keys():
                    print("\t", key, ":", invoice_details[key])

                print(">>> invoice_lines:")
                for invoice_line in invoice_lines:
                    print("\t", invoice_line)

                print(">>> invoice_tax:")
                for key in invoice_tax.keys():
                    print("\t", key, ":", invoice_tax[key])

                print(">>> invoice_totals:")
                for key in invoice_total.keys():
                    print("\t", key, ":", invoice_total[key])

            return {
                'company': template['prefix']['name'],
                'invoice_details': invoice_details,
                'invoice_lines': invoice_lines,
                'invoice_tax': invoice_tax,
                'invoice_total': invoice_total
            }


# ['', '1510727', 'STIKK.RS1091PTP.HVIT', '', 'STK', '65,06', '325,31'],
# ['', '5100', 'ELEKTRIKER', '5.5', 'TIM', '515,002', '832,50']

# ['', 'BV ',   'IDS784 4932036 PA3510E08 THERMOZONE ', '', 'STK ', '17 222 , 68 ',   '34 445 . 36 ']
# ['', 'BV ',   'IDS784 8502585 SIREACY SIRE REGULER ', '', 'STK ', '2 105 , 00 ',    '4 210 , 00 '],
# ['', 'BV ',   'SER 156 FRAKT ',                     '',   'STK ', '601 , 86 ',      '601 , 86 '],
# ['', '4100 ', 'LÆRLING ',                           '',   'TIM ', '390 , 00 ',      '20 670 , 00 '],
# ['', '5100 ', 'ELEKTRIKER ',                        '',   'TIM ', '515 , 00 ',      '26 265 , 00 ']
