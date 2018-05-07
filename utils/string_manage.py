import difflib
import math
from fuzzywuzzy import fuzz

diff = difflib.Differ()


def similarity_diff(dst_str, src_str, mode=0):
    li = list(diff.compare(dst_str, src_str))
    no_diffs, plus_diffs, minus_diffs = 0, 0, 0
    for i in range(len(li)):
        if li[i][0] == '-':
            minus_diffs += 1
        elif li[i][0] == '+':
            plus_diffs += 1
    no_diffs = len(li) - plus_diffs - minus_diffs

    if mode == 0:  # similarity based on source string
        return float(no_diffs) / float(len(src_str))
    elif mode == 1:  # similarity based on combined string
        return float(no_diffs) / float(len(li))
    elif mode == 2:  # return the same characters
        return len(no_diffs)


def similarity(dst_str, src_str):
    ratio = float(fuzz.token_set_ratio(dst_str, src_str)) / 100.0
    return ratio


def similarity_word(dst_str, src_str):
    ratio = float(fuzz.token_set_ratio(dst_str, src_str)) / 100.0
    avg_len = (len(dst_str) + len(src_str)) / 2
    sub_len = math.fabs(len(dst_str) - len(src_str)) / 2
    return ratio * (avg_len - sub_len) / avg_len


def equal(str1, str2):
    return str1.replace(' ', '').find(str2.replace(' ', '')) != -1

