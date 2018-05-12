import difflib
import math
from fuzzywuzzy import fuzz

diff = difflib.Differ()


def similarity_word(dst_str, src_str):
    ratio = float(fuzz.token_set_ratio(dst_str, src_str)) / 100.0
    avg_len = (len(dst_str) + len(src_str)) / 2
    sub_len = math.fabs(len(dst_str) - len(src_str)) / 2
    return ratio * (avg_len - sub_len) / avg_len


def equal(str1, str2):
    return str1.replace(' ', '').find(str2.replace(' ', '')) != -1

