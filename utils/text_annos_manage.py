import copy
import math
import re
from operator import itemgetter

from utils.string_manage import similarity_word

"""
    annotation = 
    {
        u'text': u'Description',
        u'boundingBox': {
            u'vertices': [
                    {u'y': 13, u'x': 8},
                    {u'y': 13, u'x': 18},
                    {u'y': 31, u'x': 18},
                    {u'y': 31, u'x': 8}]
        }
    }
"""

SAME_FONT_THRESH = 0.7  # midium
SAME_LINE_THRESH = 0.3  # small
MERGE_THRESH = 0.2  # small

EMP = ""

def __is_with_digit(word):
    word = word.replace(' ', '')
    digits = re.findall('\d+', word)
    if len(digits) != 0:
        return True
    else:
        return False


def line_ids2str(annos, ids_line):
    line_str = ""
    for id in ids_line:
        line_str += (" " + annos[id]['text'])

    return line_str


def distance_anno2anno(left, right):
    end_of_left = (left['boundingBox']['vertices'][1]['x'] + left['boundingBox']['vertices'][2]['x']) / 2
    start_of_right = (right['boundingBox']['vertices'][0]['x'] + right['boundingBox']['vertices'][3]['x']) / 2
    return start_of_right - end_of_left


def is_same_line(src_anno, dst_anno):
    src_rect = src_anno['boundingBox']['vertices']
    src_ul, src_ur, src_br, src_bl = src_rect
    src_height = get_height(anno=src_anno)
    src_cen_pt = {'x': (src_ul['x'] + src_ur['x'] + src_br['x'] + src_bl['x']) / 4,
                  'y': (src_ul['y'] + src_ur['y'] + src_br['y'] + src_bl['y']) / 4}

    dst_rect = dst_anno['boundingBox']['vertices']
    ul, ur, br, bl = dst_rect
    cen_pt = {'x': (ul['x'] + ur['x'] + br['x'] + bl['x']) / 4,
              'y': (ul['y'] + ur['y'] + br['y'] + bl['y']) / 4}

    if src_height == 0.0:
        return False

    line_ratio = math.fabs(float(src_cen_pt['y'] - cen_pt['y']) / float(src_height))
    if line_ratio < SAME_LINE_THRESH:
        return True
    else:
        return False


def is_same_font_sz(src_anno, dst_anno):
    src_height = get_height(anno=src_anno)

    height = get_height(anno=dst_anno)
    if float(src_height / 2 + height / 2) == 0:
        return False
    
    font_sz_ratio = math.fabs(float(src_height - height) / float(src_height / 2 + height / 2))
    
    if font_sz_ratio < SAME_FONT_THRESH:
        return True
    else:
        return False


def __get_left_neighbor(src_anno_id, annos):
    if src_anno_id is None:
        return None
    src_ul, src_ur, src_br, src_bl = annos[src_anno_id]['boundingBox']['vertices']
    src_left_pt = {'x': (src_ul['x'] + src_bl['x']) / 2,
                   'y': (src_ul['y'] + src_bl['y']) / 2}

    min_left_dis = None
    min_left_id = None

    for id in range(len(annos)):
        if id == src_anno_id:
            continue
        rect = annos[id]['boundingBox']['vertices']

        ul, ur, br, bl = rect
        left_r_pt = {'x': (ur['x'] + br['x']) / 2,
                     'y': (ur['y'] + br['y']) / 2}
        left_cen_pt = {'x': (ul['x'] + ur['x'] + br['x'] + bl['x']) / 4,
                       'y': (ul['y'] + ur['y'] + br['y'] + bl['y']) / 4}

        distance = src_left_pt['x'] - left_r_pt['x']
        if left_cen_pt['x'] <= src_left_pt['x'] <= left_r_pt['x']:
            distance = 0.0

        if distance >= 0 and \
                is_same_line(annos[src_anno_id], annos[id]) and is_same_font_sz(annos[src_anno_id], annos[id]):
            if min_left_id is None or min_left_dis > distance:  # find the minimum distance
                min_left_id = id
                min_left_dis = distance

    return min_left_id, min_left_dis


def __get_right_neighbor(src_anno_id, annos):
    if src_anno_id is None:
        return None
    src_ul, src_ur, src_br, src_bl = annos[src_anno_id]['boundingBox']['vertices']
    src_right_pt = {'x': (src_ur['x'] + src_br['x']) / 2,
                    'y': (src_ur['y'] + src_br['y']) / 2}
    min_right_dis = None
    min_right_id = None

    for id in range(len(annos)):
        if id == src_anno_id:
            continue
        ul, ur, br, bl = annos[id]['boundingBox']['vertices']
        right_cen_pt = {'x': (ul['x'] + ur['x'] + br['x'] + bl['x']) / 4,
                        'y': (ul['y'] + ur['y'] + br['y'] + bl['y']) / 4}
        right_l_pt = {'x': (ul['x'] + bl['x']) / 2,
                      'y': (ul['y'] + bl['y']) / 2}

        distance = right_l_pt['x'] - src_right_pt['x']
        if right_l_pt['x'] <= src_right_pt['x'] <= right_cen_pt['x']:
            distance = 0.0

        if distance >= 0 and \
                is_same_line(annos[src_anno_id], annos[id]) and is_same_font_sz(annos[src_anno_id], annos[id]):
            if min_right_id is None or min_right_dis > distance:
                min_right_dis = distance
                min_right_id = id

    return min_right_id, min_right_dis


def __get_bottom_neighbor(src_anno_id, annos):
    if src_anno_id is None:
        return None
    src_ul, src_ur, src_br, src_bl = annos[src_anno_id]['boundingBox']['vertices']
    src_bottom_pt = {'x': (src_bl['x'] + src_br['x']) / 2,
                     'y': (src_bl['y'] + src_br['y']) / 2}

    min_bottom_dis = None
    min_bottom_id = None

    for id in range(len(annos)):
        if id == src_anno_id:
            continue
        ul, ur, br, bl = annos[id]['boundingBox']['vertices']
        top_pt = {'x': (ul['x'] + ur['x'] + br['x'] + bl['x']) / 4,
                  'y': (ul['y'] + ur['y'] + br['y'] + bl['y']) / 4}

        distance = top_pt['y'] - src_bottom_pt['y']

        if src_br['x'] > top_pt['x'] > src_bl['x']:  # on the same line

            if distance >= 0 and is_same_font_sz(annos[src_anno_id], annos[id]):  # right side & same font size
                if min_bottom_id is None or min_bottom_dis > distance:
                    min_bottom_dis = distance
                    min_bottom_id = id

    return min_bottom_id, min_bottom_dis


def merge_side_words(annos, merge_thresh=MERGE_THRESH):
    cur_id = 0
    while cur_id < len(annos):
        # combine the left neighbours
        left_id, left_distance = __get_left_neighbor(src_anno_id=cur_id, annos=annos)

        while left_id is not None:
            cur_anno = annos[cur_id]
            cur_ul, cur_ur, cur_br, cur_bl = cur_anno['boundingBox']['vertices']

            left_anno = annos[left_id]
            left_ul, left_ur, left_br, left_bl = left_anno['boundingBox']['vertices']

            height = (cur_bl['y'] - cur_ul['y']) / 2 + (left_br['y'] - left_ur['y']) / 2

            if left_distance < height * merge_thresh:  # right side & same font size
                new_anno = {
                    u'text': cur_anno['text'] + " " + left_anno['text'],
                    u'boundingBox': {
                        u'vertices': [left_ul, cur_ur, cur_br, left_bl]
                    }
                }
                annos[cur_id] = new_anno
                # remove the id from the ids_line
                del annos[left_id]

                left_id, left_distance = __get_left_neighbor(src_anno_id=cur_id, annos=annos)

            else:
                break

        # combine the right neighbors
        right_id, right_distance = __get_right_neighbor(src_anno_id=cur_id, annos=annos)

        while right_id is not None:
            cur_anno = annos[cur_id]
            cur_ul, cur_ur, cur_br, cur_bl = cur_anno['boundingBox']['vertices']

            right_anno = annos[right_id]
            right_ul, right_ur, right_br, right_bl = right_anno['boundingBox']['vertices']

            height = (cur_br['y'] - cur_ur['y']) / 2 + (right_bl['y'] - right_ul['y']) / 2

            if right_distance < height * merge_thresh:  # right side & same font size
                new_anno = {
                    u'text': cur_anno['text'] + " " + right_anno['text'],
                    u'boundingBox': {
                        u'vertices': [cur_ul, right_ur, right_br, cur_bl]
                    }
                }
                annos[cur_id] = new_anno
                # remove the id from the ids_line
                del annos[right_id]

                right_id, right_distance = __get_right_neighbor(src_anno_id=cur_id, annos=annos)

            else:
                break
        cur_id += 1
    return annos


def __left_extends(parent_id, annos):
    left_child = __get_left_neighbor(src_anno_id=parent_id, annos=annos)[0]

    if left_child is not None:
        _lefts = __left_extends(parent_id=left_child, annos=annos)
        _lefts.extend([parent_id])
        return _lefts
    else:
        return [parent_id]
    

def __right_extends(parent_id, annos):
    right_child = __get_right_neighbor(src_anno_id=parent_id, annos=annos)[0]

    if right_child is not None:
        _rights = __right_extends(parent_id=right_child, annos=annos)
        _node = [parent_id]
        _node.extend(_rights)
        return _node
    else:
        return [parent_id]


def bundle_to_lines(origin_annos):
    lines = []

    annos = copy.deepcopy(origin_annos)
    annos_ids = list(range(len(annos)))

    while len(annos_ids) > 0:
        id = annos_ids[0]
        line = []

        line.extend(__left_extends(id, annos)[:])
        line.extend(__right_extends(id, annos)[1:])

        str_temp = ""
        for anno_id in line:
            str_temp += annos[anno_id]['text']

        idx = 0
        while idx < len(line):
            anno_id = line[idx]
            if anno_id not in annos_ids:
                line.remove(anno_id)
            else:
                idx += 1

        lines.append(line)

        # remove the ids from the entire annos ids
        sort_ids_line = line[:]
        sort_ids_line.sort()
        for i in range(len(sort_ids_line) - 1, -1, -1):
            if sort_ids_line[i] in annos_ids:
                annos_ids.remove(sort_ids_line[i])
                # del annos[sort_ids_line[i]]

    # sort the ids_lines with its position
    temp_lines = []
    for line in lines:
        fst_anno_pos = annos[line[0]]['boundingBox']['vertices']
        line_pos = (fst_anno_pos[0]['y'] + fst_anno_pos[3]['y']) / 2

        line_text = ""
        for anno_id in line:
            line_text += annos[anno_id]['text'] + ' '
        temp_lines.append({'line': line, 'pos': line_pos, 'text': line_text})

    sorted_lines = sorted(temp_lines, key=itemgetter('pos'))

    return sorted_lines


def find_text_lines(annos, lines):
    text_lines = []
    for ids_line in lines:
        _flag = True
        for id in ids_line:
            word = annos[id]['text']
            if __is_with_digit(word):
                _flag = False
                break
        if _flag:
            text_lines.append(ids_line)
    return text_lines


def get_left_edge(anno):
    return [(anno['boundingBox']['vertices'][0]['x'] + anno['boundingBox']['vertices'][3]['x']) / 2,
            (anno['boundingBox']['vertices'][0]['y'] + anno['boundingBox']['vertices'][3]['y']) / 2]


def get_right_edge(anno):
    return [(anno['boundingBox']['vertices'][1]['x'] + anno['boundingBox']['vertices'][2]['x']) / 2,
            (anno['boundingBox']['vertices'][1]['y'] + anno['boundingBox']['vertices'][2]['y']) / 2]


def get_val(annos, keyword, line_id, lines, info):
    if 'orientation' not in info.keys():
        orientation = 'left'
    else:
        orientation = info['orientation']
    if 'max_len' not in info.keys():
        max_len = 0
    else:
        max_len = info['max_len']

    # identify the position of keyword
    cur_text_height = get_height(anno=annos[lines[line_id]['line'][0]])

    start = 0
    end = 0
    max_similarity = 0.0

    for i in range(len(lines[line_id]['line'])):
        temp_str = EMP
        for j in range(i, len(lines[line_id]['line'])):
            cur = annos[lines[line_id]['line'][j]]
            cur_right = get_right_edge(cur)[0]

            temp_str += cur['text'] + ' '

            if j == len(lines[line_id]['line']) - 1:
                dis = 1000  # > cur_text_height * 0.7
            else:
                after = annos[lines[line_id]['line'][j + 1]]
                after_left = get_left_edge(after)[0]
                dis = after_left - cur_right

            if dis >= cur_text_height * 0.7:
                similarity = similarity_word(temp_str, keyword)
                if max_similarity < similarity:
                    start = i
                    end = j
                    max_similarity = similarity

        if max_similarity >= 0.9: break

    right_of_key = get_left_edge(annos[lines[line_id]['line'][start]])[0]
    left_of_key = get_right_edge(annos[lines[line_id]['line'][end]])[0]

    if orientation == "left":
        value = EMP
        if end < len(lines[line_id]['line']) - 1:
            end_key = annos[lines[line_id]['line'][end]]
            start_val = annos[lines[line_id]['line'][end + 1]]
            end_dis = get_left_edge(start_val)[0] - get_right_edge(end_key)[0]

            val_str = EMP
            val_width = 0
            for i in range(end + 1, len(lines[line_id]['line'])):
                cur = annos[lines[line_id]['line'][i-1]]
                cur_right = get_right_edge(cur)[0]
                after = annos[lines[line_id]['line'][i]]
                after_left = get_left_edge(after)[0]

                dis = after_left - cur_right
                if val_str == EMP or dis < cur_text_height * 2:
                    val_str += after['text'] + ' '
                    val_width += get_width(after)
                    if dis < cur_text_height * 2:
                        val_width += dis
                else:
                    break
            end_key_width = left_of_key - right_of_key
            if len(keyword) < 5:
                end_key_width *= 2.1
            if end_dis < (val_width + end_key_width) and len(val_str) > max_len:
                value = val_str

        if value == EMP:
            next_line_id = line_id + 1
            next_line_text = EMP
            for i in range(len(lines[next_line_id]['line'])):
                cur = annos[lines[next_line_id]['line'][i]]
                cur_right = get_right_edge(cur)[0]
                if get_left_edge(cur)[0] < left_of_key:
                    next_line_text = EMP
                    continue

                next_line_text += cur['text'] + " "

                if i == len(lines[next_line_id]['line']) - 1:
                    break
                else:
                    after = annos[lines[next_line_id]['line'][i + 1]]
                    after_left = get_left_edge(after)[0]
                    dis = after_left - cur_right
                    if dis > cur_text_height * 2:
                        break

            value = next_line_text

    elif orientation == "under":
        if start != 0:
            left_edge = get_right_edge(annos[lines[line_id]['line'][start - 1]])[0]
        else:
            left_edge = 0
        if end == len(lines[line_id]['line']) - 1:
            right_edge = 10000
        else:
            right_edge = get_left_edge(annos[lines[line_id]['line'][end + 1]])[0]

        next_line_id = line_id + 1
        next_line_text = EMP
        for i in range(len(lines[next_line_id]['line'])):
            cur = annos[lines[next_line_id]['line'][i]]
            cur_right = get_right_edge(cur)[0]
            if get_left_edge(cur)[0] < left_edge or get_right_edge(cur)[0] > right_edge:
                next_line_text = EMP
                continue

            next_line_text += cur['text'] + ' '
            if i == len(lines[next_line_id]['line']) - 1:
                break
            else:
                after = annos[lines[next_line_id]['line'][i + 1]]
                after_left = get_left_edge(after)[0]
                dis = after_left - cur_right
                if dis > cur_text_height * 2:
                    break

        value = next_line_text

    elif orientation == "ext_under":
        next_line_text = EMP
        i = 0
        cur_line_pos = lines[line_id]['pos']
        cur_text_height = get_height(anno=annos[lines[line_id]['line'][0]])
        while i < 2:
            i += 1
            next_line_id = line_id + i
            next_line_pos = lines[next_line_id]['pos']

            dis = next_line_pos - cur_line_pos
            if cur_text_height * 5 < dis or next_line_id >= len(lines) - 1:
                break
            else:
                for idx in range(0, len(lines[next_line_id]['line'])):
                    val_anno = annos[lines[next_line_id]['line'][idx]]
                    next_line_text += val_anno['text'] + ' '
        value = next_line_text

    elif orientation == "ext_upper":
        upper_line_text = EMP

        i = 0
        cur_line_pos = lines[line_id]['pos']
        cur_text_height = get_height(anno=annos[lines[line_id]['line'][0]])
        while i < 2:
            i += 1
            upper_line_id = line_id - i
            upper_line_pos = lines[upper_line_id]['pos']

            dis = cur_line_pos - upper_line_pos
            if cur_text_height * 5 < dis or upper_line_id <= 0:
                break
            else:
                for idx in range(0, len(lines[upper_line_id]['line'])):
                    val_anno = annos[lines[upper_line_id]['line'][idx]]
                    upper_line_text += val_anno['text'] + ' '
        value = upper_line_text

    else:
        value = ""

    if len(value) >= max_len:
        return clear_value(value)
    else:
        return ""


def get_height(anno):
    _ul, _ur, _br, _bl = anno['boundingBox']['vertices']
    return (_bl['y'] - _ul['y'] + _br['y'] - _ur['y']) / 2


def get_width(anno):
    _ul, _ur, _br, _bl = anno['boundingBox']['vertices']
    return (_ur['x'] - _ul['x'] + _br['x'] - _bl['x']) / 2


def clear_value(str_value):
    for ch in ['-', ':']:
        if ch in str_value:
            str_value = str_value.replace(ch, '')
    return str_value


def is_candi_line(text):
    digits = re.findall('\d+', text)
    alphabets = " ".join(re.findall("[a-zA-Z]+", text))
    return (len(digits) + len(alphabets)) != 0


def str2val(word):
    word = __get_digits(word)
    if word == EMP:
        return -1
    else:
        word = word.replace(' ', '')
        word = word.replace(',', '.')
        try:
            val = float(word)
            return val
        except Exception as e:
            print(e)
            return -1


def __get_digits(word):
    word = word.replace(' ', '')
    tmp = word
    tmp = tmp.replace(',', '0')
    tmp = tmp.replace('.', '0')
    digits = re.findall('\d+', tmp)
    if len(digits) == 0:
        return EMP

    max_di = ""
    for di in digits:
        if len(di) > len(max_di):
            max_di = di

    pos = tmp.find(max_di)
    if pos != -1:
        return word[pos: pos+len(max_di)]
    else:
        return EMP
