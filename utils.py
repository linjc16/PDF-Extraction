import re
import cv2
import os
import numpy as np
import pdb

def re_match_index(text, type):
    signs = ['figure', 'fig.', 'fig'] if type == 'figure' else ['table']
    
    for sign in signs:
        reg = []
        reg.append(r"(?<={} )\d+".format(sign))
        reg.append(r"(?<={} )[a-z]+".format(sign))
        reg.append(r"(?<={})\d+".format(sign))
        reg.append(r"(?<={})[a-z]+".format(sign))
    
        reg = "|".join(reg)
        index = re.findall(reg, text, re.I)
        
        if len(index) > 0:
            break

    prefix = ''
    if len(index) > 0:
        prefix = text.split(index[0])[0]
    
    # pdb.set_trace()
    return (index[0], prefix + index[0]) if len(index) > 0 and len(prefix) < 10 else (None, None)

def topk_nearest_bbox(tb_bbox, text_bboxes, k):
    above_dist = []
    below_dist = []

    for text_bbox in text_bboxes:
        dist_ab = abs(tb_bbox[0] - text_bbox[0]) + abs(tb_bbox[1] - text_bbox[3])
        above_dist.append(dist_ab)
        dist_bl = abs(tb_bbox[0] - text_bbox[0]) + abs(tb_bbox[3] - text_bbox[1])
        below_dist.append(dist_bl)

    above_idx = sorted(enumerate(above_dist), key=lambda x:x[1])
    below_idx = sorted(enumerate(below_dist), key=lambda x:x[1])
    
    return above_idx[0:k], below_idx[0:k]


def check_and_read(img_path):
    if os.path.basename(img_path)[-3:] in ['pdf']:
        import fitz
        from PIL import Image
        imgs = []
        with fitz.open(img_path) as pdf:
            for pg in range(0, pdf.page_count):
                page = pdf[pg]
                mat = fitz.Matrix(8, 8)
                pm = page.get_pixmap(matrix=mat, alpha=False)
                # import pdb
                # pdb.set_trace()

                # if width or height > 2000 pixels, don't enlarge the image
                if pm.width > 8000 or pm.height > 8000:
                    pm = page.get_pixmap(matrix=fitz.Matrix(4, 4), alpha=False)

                img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
                img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                imgs.append(img)
            return imgs, False, True
    return None, False, False
if __name__ == '__main__':
    print(re_match_index('TAble II. ', 'table'))