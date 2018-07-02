import logger as log
import utils.string_manage as stringer
import utils.text_annos_manage as manager
from utils.template import Template
from utils.validate import Validate
from utils.settings import *


EMP = ""
SPLITER = "_/SP/_"
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
        components = template['info']['InvoiceDetails']
        ret_dict = {}
        for component in components:
            ret_dict[component['meaning']] = EMP

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
            if 'multi_lines' in template['info']['InvoiceLines'].keys():
                multi_line_component_sets = template['info']['InvoiceLines']['multi_lines']
            else:
                multi_line_component_sets = []

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
            mul_line_1st_item_ids = []
            line_total_id = -1
            line_discount_id = -1
            if len(main_keyanno_list) != -1:
                ###################################################
                # --- find the multi-line item's index ---
                for mul_line_set in multi_line_component_sets:
                    meaning_1, meaning_2 = mul_line_set[:2]
                    meaning_1_keywords, meaning_2_keywords = [], []

                    for component in components:
                        if component['meaning'] == meaning_1:
                            meaning_1_keywords = component['keywords']
                            break
                    # for component in components:
                    #     if component['meaning'] == meaning_2:
                    #         meaning_2_keywords = component['keywords']

                    for k in range(len(main_keyanno_list)):
                        key_anno = main_keyanno_list[k]
                        if key_anno['keyword'] in meaning_1_keywords:
                            mul_line_1st_item_ids.append(k)
                            break
                # --- find the total keyword index in a line ---
                line_total_keywords = []
                for component in components:
                    if component['meaning'] == "TotalLineAmount":
                        line_total_keywords = component['keywords']
                        break
                for k in range(len(main_keyanno_list)):
                    key_anno = main_keyanno_list[k]
                    if key_anno['keyword'] in line_total_keywords:
                        line_total_id = k
                        break

                # --- find the discount keyword index in a line ---
                for component in components:
                    if component['meaning'] == "Discount":
                        line_discount_id = components.index(component)  # index of filled line
                ###################################################

                if self.debug:
                    img = content['image']
                    for key_anno in main_keyanno_list:
                        pt1 = key_anno['left']
                        pt2 = key_anno['right']
                        img = cv2.line(img, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[1])), (0, 0, 255), 10)
                    content['image'] = img

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
                    if dis > manager.get_height(annos[lines[key_line_pos]['line'][0]]) * 5:
                        break
                    filtered_lines.append(cur_line)
                    line_id += 1

                # in filtered lines, the keyword_line is the first line
                key_line_pos = 0
                lines = filtered_lines
            # --- config the lines ---------------------------------------------------
            value_lines = []
            if len(main_keyanno_list) != -1:
                cnt_false_lines = 0
                for line_id in range(key_line_pos + 1, len(lines)):
                    line = lines[line_id]['line']
                    line_discount_val = EMP

                    value_line = [EMP] * len(main_keyanno_list)
                    start = 0
                    for k in range(0, len(main_keyanno_list)):
                        temp_str = EMP
                        if k == 0:  # first annotation
                            for i in range(start, len(line)):
                                if annos[line[i]]['used']: continue
                                if manager.get_right_edge(annos[line[i]])[0] <= main_keyanno_list[k+1]['left'][0]:
                                    temp_str += annos[line[i]]['text'] + ' '
                                    annos[line[i]]['used'] = True
                                else:
                                    start = i
                                    value_line[k] = temp_str
                                    break
                        elif k != len(main_keyanno_list) - 1:  # middle annotations
                            for i in range(start, len(line)):
                                if annos[line[i]]['used']: continue
                                if main_keyanno_list[k - 1]['right'][0] <= manager.get_left_edge(annos[line[i]])[0] and\
                                            manager.get_right_edge(annos[line[i]])[0] < main_keyanno_list[k + 1]['left'][0]:

                                    if i != len(line) - 1 and manager.distance_anno2anno(left=annos[line[i]], right=annos[line[i + 1]]) < 3 * manager.get_height(annos[lines[key_line_pos]['line'][0]]):
                                        temp_str += annos[line[i]]['text'] + ' '
                                        annos[line[i]]['used'] = True
                                    else:
                                        temp_str += annos[line[i]]['text'] + ' '
                                        if manager.is_line_discount(temp_str):
                                            line_discount_val = temp_str
                                            temp_str = EMP
                                            annos[line[i]]['used'] = True
                                            continue
                                        annos[line[i]]['used'] = True
                                        value_line[k] = temp_str
                                        start = i + 1
                                        break
                                else:
                                    start = i
                                    value_line[k] = temp_str
                                    break
                        elif k == len(main_keyanno_list) - 1:  # last annotation
                            for i in range(start, len(line)):
                                if annos[line[i]]['used']: continue
                                if main_keyanno_list[k-1]['right'][0] < manager.get_left_edge(annos[line[i]])[0]:
                                    temp_str += annos[line[i]]['text'] + ' '
                                    annos[line[i]]['used'] = True
                            value_line[k] = temp_str

                    num_emptys = value_line.count(EMP)
                    if len(value_line) - num_emptys > THRESH_MIN_LINE_KEYS:
                        if line_discount_id != -1:
                            value_line.append(line_discount_val)
                        value_lines.append(value_line)

                    else:
                        if len(value_line) >= line_total_id + 1 and num_emptys == len(value_line) - 2 and \
                                value_line[mul_line_1st_item_ids[-1]] != EMP and value_line[line_total_id] != EMP:
                            if line_discount_id != -1:
                                value_line.append(line_discount_val)
                            value_lines.append(value_line)
                            continue
                        elif num_emptys >= len(value_line) - 2 and len(value_lines) > 0:
                            for mul_line_1st_item_id in mul_line_1st_item_ids:
                                if value_line[mul_line_1st_item_id] != EMP and value_lines[-1][mul_line_1st_item_id] != EMP:
                                    value_lines[-1][mul_line_1st_item_id] += SPLITER + value_line[mul_line_1st_item_id]
                            continue
                        elif lines[line_id]['pos'] - lines[key_line_pos]['pos'] < manager.get_height(anno=annos[lines[key_line_pos]['line'][0]]) * 3:
                            continue
                        else:
                            for i in range(len(line)):
                                if annos[line[i]]['used']: annos[line[i]]['used'] = False  # restore the wrong line
                            cnt_false_lines += 1
                            if cnt_false_lines > 2:
                                break

            # --- fillout the value line with order of components
            if len(value_lines) != 0:

                filled_lines = []
                for value_line in value_lines:
                    # init the empty contrainer for result dict
                    filled_line = [EMP] * len(components)
                    filled_line[0] = str(value_lines.index(value_line) + len(total_value_lines) + 1)  # line id = filled line index

                    for i in range(1, len(components)):
                        component = components[i]
                        for k in range(len(main_keyanno_list)):
                            key_anno = main_keyanno_list[k]
                            if key_anno['keyword'] in component['keywords']:
                                filled_line[i] = value_line[k]
                                break

                        # last element of the value line is the discount percent
                        if line_discount_id != -1 and len(value_line) == len(main_keyanno_list) + 1:
                            filled_line[line_discount_id] = value_line[-1]

                    # fix the multi-line values
                    if len(multi_line_component_sets) != 0:
                        for mul_line_set in multi_line_component_sets:
                            meaning_1, meaning_2 = mul_line_set[:2]
                            for i in range(len(components)):
                                if components[i]['meaning'] == meaning_1:
                                    id1 = i
                                if components[i]['meaning'] == meaning_2:
                                    id2 = 2

                            if not id1 or not id2:
                                continue
                            if filled_line[id1] != EMP:
                                sps = filled_line[id1].split(SPLITER)
                                if len(sps) >= 2 and filled_line[id1] != EMP:
                                    if id1 == id2:
                                        filled_line[id1] = sps[0] + " " + sps[1]
                                    if id1 != id2:
                                        filled_line[id1] = sps[0]
                                        filled_line[id2] = sps[1]

                    filled_lines.append(filled_line)

                total_value_lines.extend(filled_lines)

        return total_value_lines

    def get_total_infos(self, template, contents):
        totals = template['info']['Totals']
        components = totals['components']
        orientation = totals['orientation']

        ret_dict = {}
        for content in contents:  # get total info from the last page
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
                        # pos = line_text.replace(' ', '').find(keyword.replace(' ', ''))
                        pos = stringer.find_keyword(line_text, keyword)
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
        log.log_print("\t recognize the document type")
        template = self.recognize_template_id(content=contents[0])

        if template is None:  # unknown document type
            log.log_print("\tunknown document type.\n")
            return template, {'error': "unknown document type."}
        else:
            log.log_print("\t\ttemplate: {}\n".format(template['prefix']['name']))
            invoice_details = self.get_details_infos(template=template, contents=contents)
            invoice_tax = self.get_tax_infos(template=template, contents=contents)
            invoice_total = self.get_total_infos(template=template, contents=contents)
            invoice_lines = self.get_line_infos(template=template, contents=contents)

            info = {
                'company': template['prefix']['name'],
                'invoice_details': invoice_details,
                'invoice_lines': invoice_lines,
                'invoice_tax': invoice_tax,
                'invoice_total': invoice_total
            }

            return template, info
