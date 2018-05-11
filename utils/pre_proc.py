import imutils
import math
import cv2
import numpy as np
import logger as log
from utils.text_annos_manage import *
import sys


class PreProc:
    def __init__(self, debug=False):
        self.debug = debug

    def __rect_angle(self, anno):
        points = anno['boundingBox']['vertices']

        centerX = .0
        centerY = .0
        for i in range(4):
            if 'x' not in points[i].keys():
                points[i]['x'] = 0
            if 'y' not in points[i].keys():
                points[i]['y'] = 0
            centerX += points[i]['x'] / 4
            centerY += points[i]['y'] / 4
        x0 = points[0]['x']
        y0 = points[0]['y']

        if x0 < centerX and y0 < centerY:
            angle = 0.0
            for i in range(4):
                dx = points[(i + 1) % 4]['x'] - points[i]['x']
                dy = points[(i + 1) % 4]['y'] - points[i]['y']
                _atan = math.atan2(dy, dx)
                if _atan < 0: _atan += math.pi * 2
                radian = i * math.pi / 2 - _atan

                if radian < -math.pi:
                    radian += math.pi * 2
                elif radian > math.pi:
                    radian -= math.pi * 2

                angle += radian
            return angle / 4
        else:
            return None

    def pre_proc(self, content):
        # self.align(content=content)
        # self.crop(content=content)
        self.config_lines(content=content)

        if self.debug:
            sys.stdout.write("\tlines:\n")
            for line in content['lines']:
                sys.stdout.write("\t\t{}\n".format(line['text']))

            # draw rectangle of the annotation
            image = content['image']
            for anno in content['annos']:
                points = anno['boundingBox']['vertices']
                for i in range(0, 3):
                    image = cv2.line(image, (points[i]['x'], points[i]['y']), (points[i + 1]['x'], points[i + 1]['y']),
                                     (200, 0, 0), 2)
            content['image'] = image

    def align(self, content):
        deg_angle = self.__calc_angle(annos=content['annotations'])

        # rotate the image
        rotated = imutils.rotate(content['image'], deg_angle)
        content['image'] = rotated

        # update the annoataion rects with angles
        image = content['image']
        height, width = image.shape[:2]
        cen_pt = (width / 2, height / 2)
        for anno in content['annotations']:
            points = anno['boundingBox']['vertices']
            for point in points:
                new_pt = self.__rotate_pt(pt=(point['x'], point['y']), cen_pt=cen_pt, angle=deg_angle)
                point['x'] = new_pt[0]
                point['y'] = new_pt[1]

    def __rotate_pt(self, pt, cen_pt, angle):
        angle = math.radians(-angle)
        dx = pt[0] - cen_pt[0]
        dy = pt[1] - cen_pt[1]

        new_dx = dx * math.cos(angle) - dy * math.sin(angle)
        new_dy = dx * math.sin(angle) + dy * math.cos(angle)

        new_x = new_dx + cen_pt[0]
        new_y = new_dy + cen_pt[1]
        return [int(new_x), int(new_y)]

    def __calc_angle(self, annos):
        # calculate the rotated angle
        avg_angle = .0
        cnt = 0
        for anno in annos:
            angle = self.__rect_angle(anno)
            if angle is not None:
                cnt += 1
                avg_angle += angle

        avg_angle /= cnt
        avg_angle_deg = avg_angle * 180 / math.pi
        log.log_print("\tangle to be Rotated: {}(deg)".format(avg_angle_deg))
        return -avg_angle_deg

    def crop(self, content):
        # crop the image based on max and minimum position of annos
        image = content['image']
        height, width = image.shape[:2]

        # find the border of the page entity
        left, top, right, bottom = width / 2, height / 2, width / 2, height / 2
        max_h = 0

        annos = content['annotations']
        for anno in annos:
            ul, ur, br, bl = anno['boundingBox']['vertices']
            _li_x = [ul['x'], ur['x'], br['x'], bl['x']]
            _li_y = [ul['y'], ur['y'], br['y'], bl['y']]

            left = min(min(_li_x), left)
            right = max(max(_li_x), right)
            top = min(min(_li_y), top)
            bottom = max(max(_li_y), bottom)

            max_h = max(max_h, math.fabs(bl['y']-ul['y']), math.fabs(br['y']-ur['y']))

        left = int(max(left - max_h, 0))
        top = int(max(top - max_h, 0))
        right = int(min(right + max_h, width))
        bottom = int(min(bottom + max_h, height))

        crop = image[top:bottom, left:right]
        content['image'] = crop

        # update the annos with new crop size
        for anno in annos:
            points = anno['boundingBox']['vertices']
            new_points = [{'x': point['x'] - left, 'y': point['y'] - top} for point in points]
            anno['boundingBox']['vertices'] = new_points

    def config_lines(self, content):
        annos = content['annos']
        lines = bundle_to_lines(annos)

        content['lines'] = lines

