import os
import cv2
import json
import re
from copy import deepcopy

from paddleocr import PPStructure, PaddleOCR
# from paddleocr.paddleocr import parse_args
from paddleocr.ppstructure.predict_system import save_structure_res
from paddleocr.ppstructure.utility import draw_structure_result
from paddleocr.ppstructure.table.predict_table import to_excel

from paddleocr.ppocr.utils.logging import get_logger
logger = get_logger()

from paddleocr.ppocr.utils.utility import get_image_file_list
from utils import check_and_read

from paddleocr.ppstructure.utility import init_args
from paddleocr.tools.infer.utility import draw_ocr, str2bool, check_gpu
SUPPORT_OCR_MODEL_VERSION = ['PP-OCR', 'PP-OCRv2', 'PP-OCRv3']
SUPPORT_STRUCTURE_MODEL_VERSION = ['PP-Structure', 'PP-StructureV2']

import pdb

def parse_args(mMain=True):
    import argparse
    parser = init_args()
    parser.add_help = mMain
    parser.add_argument("--lang", type=str, default='ch')
    parser.add_argument("--det", type=str2bool, default=True)
    parser.add_argument("--rec", type=str2bool, default=True)
    parser.add_argument("--type", type=str, default='ocr')

    parser.add_argument('--src', type=str, help='Paper domain, such as biorxiv or medrxiv')
    parser.add_argument('--n_jobs', type=int, help='Number of parallel jobs')
    parser.add_argument('--out_root_dir', type=str, help='Saved folder path')
    parser.add_argument('--filtered', default=False, action='store_true', help='Using the txt files containing pdf filename list')
    parser.add_argument('--paper_list_filepath', type=str, help='Txt files containing pdf filename list')

    parser.add_argument('--nproc_per_node', type=int, default=1)
    parser.add_argument('--node_rank', type=int, default=0)
    parser.add_argument('--local_rank', type=int, default=0)
    parser.add_argument('--nnodes', type=int, default=1)
    parser.add_argument('--master_addr', type=str, default='127.0.0.1')
    parser.add_argument('--master_port', type=int, default=8000)


    for action in parser._actions:
        if action.dest in [
                'rec_char_dict_path', 'table_char_dict_path', 'layout_dict_path'
        ]:
            action.default = None
    if mMain:
        return parser.parse_args()
    else:
        inference_args_dict = {}
        for action in parser._actions:
            inference_args_dict[action.dest] = action.default
        return argparse.Namespace(**inference_args_dict)

class PdfPaddleOCR():
    def __init__(self, pdf_dir=None, process_type=None, output=None):
        self.num_table = 0
        self.num_fig = 0
        self.table_mode = None

        self.image_dir = pdf_dir
        self.type = process_type
        self.output = output

        self.table_list = []
        self.fig_list = []
        self.data = {}

    def reset(self, pdf_dir, process_type, output):
        self.num_table = 0
        self.num_fig = 0
        self.table_mode = None

        self.image_dir = pdf_dir
        self.type = process_type
        self.output = output

        self.table_list = []
        self.fig_list = []
        self.data = {}

    def re_match_index(self, text, type):
        signs = ['figure', 'fig.'] if type == 'figure' else ['table']
        reg = []

        for sign in signs:
            # for i in range(len(sign) - 3):
            reg.append(r"(?<={})\d+".format(sign))
            reg.append(r"(?<={} )\d+".format(sign))
        
        reg = "|".join(reg)
        index = re.findall(reg, text.lower())

        return index[0] if len(index) > 0 else None

    def nearest_bbox_matching(self, res_text, region, caption_index):
        bbox_obj = region['bbox']
        above_dist = []
        below_dist = []

        for region_text in res_text:
            bbox_text = region_text['bbox']
            dist_ab = abs(bbox_obj[0] - bbox_text[0]) + abs(bbox_obj[1] - bbox_text[3])
            above_dist.append(dist_ab)
            dist_bl = abs(bbox_obj[0] - bbox_text[0]) + abs(bbox_obj[3] - bbox_text[1])
            below_dist.append(dist_bl)

        above_idx = sorted(enumerate(above_dist), key=lambda x:x[1])
        below_idx = sorted(enumerate(below_dist), key=lambda x:x[1])

        for count, idx in enumerate(above_idx):
            if self.table_mode == 'below':
                break
            # pdb.set_trace()
            for text_block in res_text[idx[0]]['res']:
                obj_index = self.re_match_index(text_block['text'], region['type'].lower())
                
                if obj_index is not None and obj_index == caption_index:
                    if self.table_mode is None:
                        self.table_mode = 'above'
                    return region['type'] + str(obj_index)
        
        for count, idx in enumerate(below_idx):
            if self.table_mode == 'above':
                break
            for text_block in res_text[idx[0]]['res']:
                obj_index = self.re_match_index(text_block['text'], region['type'])
    
                if obj_index is not None and obj_index == caption_index:
                    if self.table_mode is None:
                        self.table_mode = 'below'
                    return region['type'] + str(obj_index)
        
        return region['type'] + str(caption_index)

    def save_structure_match_res(self, res, save_folder, img_name, img_idx=0):
        excel_save_folder = os.path.join(save_folder, img_name)
        os.makedirs(excel_save_folder, exist_ok=True)
        res_cp = deepcopy(res)

        # text region
        res_text = [region for region in res_cp if region['type'].lower() == 'text']


        # save res
        with open(
                os.path.join(excel_save_folder, 'res_{}.txt'.format(img_idx)),
                'w',
                encoding='utf8') as f:
            for region in res_cp:
                roi_img = region.pop('img')
                f.write('{}\n'.format(json.dumps(region)))

                if region['type'].lower() == 'table' and len(region[
                        'res']) > 0 and 'html' in region['res']:
                    self.num_table += 1
                    excel_path = os.path.join(
                        excel_save_folder,
                        '{}_{}_{}.xlsx'.format(self.nearest_bbox_matching(res_text, region, self.num_table), region['bbox'], img_idx))
                    to_excel(region['res']['html'], excel_path)
                    fig_path = os.path.join(
                        excel_save_folder,
                        '{}_{}_{}.png'.format(self.nearest_bbox_matching(res_text, region, self.num_table), region['bbox'], img_idx))
                    cv2.imwrite(fig_path, roi_img, [cv2.IMWRITE_JPEG_QUALITY,100])
                    self.table_list.append({
                        'tb': excel_path,
                        'fig': fig_path
                    })
                
                elif region['type'].lower() == 'figure':
                    # if img_idx == 10:
                    #     pdb.set_trace()
                    self.num_fig += 1
                    img_path = os.path.join(
                        excel_save_folder,
                        '{}_{}_{}.png'.format(self.nearest_bbox_matching(res_text, region, self.num_fig), region['bbox'], img_idx))
                    cv2.imwrite(img_path, roi_img, [cv2.IMWRITE_JPEG_QUALITY,100])
                    self.fig_list.append({
                        'fig': img_path
                    })

        # pdb.set_trace()

    def run(self):
        args = parse_args(mMain=True)
        args.image_dir = self.image_dir
        args.type = self.type
        args.output = self.output
        args.lang = 'en'

        image_dir = args.image_dir
        image_file_list = get_image_file_list(args.image_dir)
        if len(image_file_list) == 0:
            logger.error('no images find in {}'.format(args.image_dir))
            return
        if args.type == 'ocr':
            engine = PaddleOCR(**(args.__dict__))
        elif args.type == 'structure':
            engine = PPStructure(**(args.__dict__))
        else:
            raise NotImplementedError
        
        num_table, num_fig = 0, 0
        
        for img_path in image_file_list:
            img_name = '.'.join(os.path.basename(img_path).split('.')[:-1])
            # pdb.set_trace()
            logger.info('{}{}{}'.format('*' * 10, img_path, '*' * 10))
            if args.type == 'ocr':
                result = engine.ocr(img_path,
                                    det=args.det,
                                    rec=args.rec,
                                    cls=args.use_angle_cls)
                if result is not None:
                    for idx in range(len(result)):
                        res = result[idx]
                        for line in res:
                            logger.info(line)
            elif args.type == 'structure':
                img, flag_gif, flag_pdf = check_and_read(img_path)
                # pdb.set_trace()
                if not flag_gif and not flag_pdf:
                    img = cv2.imread(img_path)

                # if args.recovery and args.use_pdf2docx_api and flag_pdf:
                #     from pdf2docx.converter import Converter
                #     docx_file = os.path.join(args.output,
                #                              '{}.docx'.format(img_name))
                #     cv = Converter(img_path)
                #     cv.convert(docx_file)
                #     cv.close()
                #     logger.info('docx save to {}'.format(docx_file))
                #     continue

                if not flag_pdf:
                    if img is None:
                        logger.error("error in loading image:{}".format(img_path))
                        continue
                    img_paths = [[img_path, img]]
                else:
                    # pdb.set_trace()
                    img_paths = []
                    for index, pdf_img in enumerate(img):
                        os.makedirs(
                            os.path.join(args.output, img_name), exist_ok=True)
                        pdf_img_path = os.path.join(
                            args.output, img_name,
                            img_name + '_' + str(index) + '.png')
                        cv2.imwrite(pdf_img_path, pdf_img, [cv2.IMWRITE_JPEG_QUALITY,100])
                        img_paths.append([pdf_img_path, pdf_img])

                # pdb.set_trace()
                all_res = []
                for index, (new_img_path, img) in enumerate(img_paths):
                    logger.info('processing {}/{} page:'.format(index + 1,
                                                                len(img_paths)))
                    new_img_name = os.path.basename(new_img_path).split('.')[0]
                    result = engine(new_img_path, img_idx=index)
                    # pdb.set_trace()
                    self.save_structure_match_res(result, args.output, img_name, index)
                
                    # if args.recovery and result != []:
                    #     from copy import deepcopy
                    #     from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes
                    #     h, w, _ = img.shape
                    #     result_cp = deepcopy(result)
                    #     result_sorted = sorted_layout_boxes(result_cp, w)
                    #     all_res += result_sorted
                
                # if args.recovery and all_res != []:
                #     try:
                #         from paddleocr.ppstructure.recovery.recovery_to_doc import convert_info_docx
                #         convert_info_docx(img, all_res, args.output, img_name)
                #     except Exception as ex:
                #         logger.error(
                #             "error in layout recovery image:{}, err msg: {}".format(
                #                 img_name, ex))
                #         continue

                for item in all_res:
                    item.pop('img')
                    item.pop('res')
                    logger.info(item)
                logger.info('result save to {}'.format(args.output))

                self.data['table'] = self.table_list
                self.data['figure'] = self.fig_list
      
        return self.data
    
if __name__ == '__main__':
    ppocr = PdfPaddleOCR('pdf_example/antibody.pdf', 'structure', 'out')
    data = ppocr.run()
