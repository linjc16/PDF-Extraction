import os
import json
import argparse
from collections import defaultdict
import glob
import fitz
from tqdm import tqdm
from utils import topk_nearest_bbox, re_match_index
from fuzzywuzzy import fuzz, process
import re
import multiprocessing as mp
import pdb

FIGURE_PREFIX = ['Figure', 'Fig', 'Fig.']
TABLE_PREFIX = ['Table']

def match_table_caption(table, text_list, pdf_text):
    '''
        Match the table and the caption which are in the same page.
        Input:
            table: dict{type, bbox, res, img_idx}
            text_list: List[dict{type, bbox, res, img_idx}]
            pdf_text: str
        Output:
            Dict{html, caption, passage}
    '''
    out = {}
    tb_bbox = table['bbox']
    text_bboxes = [text['bbox'] for text in text_list]
    above_idx, below_idx = topk_nearest_bbox(tb_bbox, text_bboxes, k=2)

    pdf_text = pdf_text.split('\n')
    pure_id, tb_index = None, None
    
    above_idx.extend(below_idx)
    # print(above_idx)
    refined_text = None
    merged_text = None

    for ab_out in above_idx:
        caption_text = text_list[ab_out[0]]
        merged_text = [item['text'] for item in caption_text['res']]
        if len(merged_text) == 0:
            continue

        # print(f'merged text: {merged_text}')

        refined_text = [process.extractOne(text, pdf_text) for text in merged_text]
        refined_text = [item[0] for item in refined_text]
        
        # deduplicate
        refined_text_temp = []
        for text_src in refined_text:
            flag_dup = False
            for text_tgt in refined_text_temp:
                if fuzz.partial_ratio(text_src, text_tgt) > 90:
                    flag_dup = True
                    break
            if not flag_dup:
                refined_text_temp.append(text_src)
        
        refined_text = refined_text_temp
        refined_text = ' '.join(refined_text)
        # print(f'refined text: {refined_text}')

        pure_id, tb_index = re_match_index(refined_text, 'table')
        if tb_index is not None:
            break
    # print(tb_index)
    # pdb.set_trace()
    out['pure_id'] = pure_id
    out['id'] = tb_index
    out['caption'] = refined_text
    out['ocr_caption'] = ' '.join(merged_text) if merged_text is not None else None
    out['html'] = table['res']['html']
    out['bbox'] = table['bbox']
    out['img_idx'] = table['img_idx']
    return out

def match_figure_caption(fig, text_list, pdf_text):
    '''
        Match the figure and the caption which are in the same page.
        Input:
            fig: dict{type, bbox, res, img_idx}
            text_list: List[dict{type, bbox, res, img_idx}]
            pdf_text: str
        Output:
            Dict{html, caption, passage}
    '''
    out = {}
    fig_bbox = fig['bbox']
    text_bboxes = [text['bbox'] for text in text_list]
    above_idx, below_idx = topk_nearest_bbox(fig_bbox, text_bboxes, k=2)

    pdf_text = pdf_text.split('\n')
    pure_id, fig_index = None, None
    
    below_idx.extend(above_idx)
    # print(below_idx)

    refined_text = None
    merged_text = None

    for bl_out in below_idx:
        caption_text = text_list[bl_out[0]]
        merged_text = [item['text'] for item in caption_text['res']]
        if len(merged_text) == 0:
            continue

        # print(f'merged text: {merged_text}')

        refined_text = [process.extractOne(text, pdf_text) for text in merged_text]
        refined_text = [item[0] for item in refined_text]

        # deduplicate
        refined_text_temp = []
        for text_src in refined_text:
            flag_dup = False
            for text_tgt in refined_text_temp:
                if fuzz.partial_ratio(text_src, text_tgt) > 85:
                    flag_dup = True
                    break
            if not flag_dup:
                refined_text_temp.append(text_src)
        
        refined_text = refined_text_temp
        refined_text = ' '.join(refined_text)
        # print(f'refined text: {refined_text}')

        pure_id, fig_index = re_match_index(refined_text, 'figure')
        if fig_index is not None:
            break
    # print(fig_index)
    # pdb.set_trace()
    out['pure_id'] = pure_id
    out['id'] = fig_index
    out['caption'] = refined_text
    out['ocr_caption'] = ' '.join(merged_text) if merged_text is not None else None
    out['bbox'] = fig['bbox']
    out['img_idx'] = fig['img_idx']
    return out

def refine_text_with_pdf(ocr_text, doc):
    """
        Refine the ocr text with pdf text.
        Input:
            orc_text: Dict[dict{type, bbox, res, img_idx}]
            doc: Document class in Pymupdf
    """
    out = []
    for page in range(len(ocr_text)):
        ocr_page_text = ocr_text[page]
        pdf_page_text = doc.load_page(page).get_text('text').split('\n')
        pdf_page_text = list(filter(None, pdf_page_text))
        
        ocr_page_text = [[item['text'] for item in text_list['res']] for text_list in ocr_page_text]
        refined_text = [' '.join([process.extractOne(sentence, pdf_page_text)[0] for sentence in para_text if sentence != '']) for para_text in ocr_page_text]
        refined_text = list(filter(None, refined_text))
        refined_text = [item.rstrip() for item in refined_text]
        if len(refined_text) > 0:
            out.append(refined_text) 
    
    
    return out

def make_samples(args, raw_data_path, raw_out, pdf_path):
    out_sample = {}
    out_sample['src'] = args.src
    out_sample['paper_id'] = raw_out
    out_sample['pdf_path'] = pdf_path

    # Read the pdf file
    doc = fitz.Document(pdf_path)

    text = defaultdict(list)
    figures = defaultdict(list)
    tables = defaultdict(list)
    res_list = glob.glob(os.path.join(raw_data_path, raw_out, 'res*.txt'))
    fig_list = glob.glob(os.path.join(raw_data_path, raw_out, 'figure*.png'))
    tb_list = glob.glob(os.path.join(raw_data_path, raw_out, 'table*.xlsx'))
    tb_fig_list = glob.glob(os.path.join(raw_data_path, raw_out, 'table*.png'))
    
    for page in range(len(res_list)):
        with open(os.path.join(raw_data_path, raw_out, f'res_{page}.txt'), 'r', encoding='utf8') as f:
            samples = f.readlines()
            for sample in samples:
                sample = json.loads(sample)
                if sample['type'] == 'table':
                    tables[page].append(sample)
                elif sample['type'] == 'figure':
                    figures[page].append(sample)
                else:
                    text[page].append(sample)
            f.close()
    
    tb_data = []
    fig_data = []

    tb_basenames = [os.path.basename(item) for item in tb_list]
    tb_fig_basenames = [os.path.basename(item) for item in tb_fig_list]
    fig_basenames = [os.path.join(item) for item in fig_list]

    for page in tables.keys():
        print(f'Processing tables in page {page}/{len(res_list)}.')
        page_content = doc.load_page(page)
        page_text = page_content.get_text('text')
        for table in tables[page]:
            tb_out = defaultdict()
            out = match_table_caption(table, text[page], page_text)
            bbox, img_idx = table['bbox'], table['img_idx']
            tb_filename = [item for item in tb_basenames if f'{bbox}_{img_idx}' in item][0]
            tb_fig_filename = [item for item in tb_fig_basenames if f'{bbox}_{img_idx}' in item][0]
            tb_out['excel_path'] = os.path.join(raw_data_path, raw_out, tb_filename)
            tb_out['fig_path'] = os.path.join(raw_data_path, raw_out, tb_fig_filename)
            tb_out.update(out)
            tb_data.append(tb_out)
            # pdb.set_trace()
    
    for page in figures.keys():
        print(f'Processing figures in page {page + 1}/{len(res_list)}.')
        page_content = doc.load_page(page)
        page_text = page_content.get_text('text')
        for fig in figures[page]:
            fig_out = defaultdict()
            out = match_figure_caption(fig, text[page], page_text)
            bbox, img_idx = fig['bbox'], fig['img_idx']
            fig_filename = [item for item in fig_basenames if f'{bbox}_{img_idx}' in item]
            if len(fig_filename) > 0:
                fig_filename = fig_filename[0]
                fig_out['fig_path'] = os.path.join(raw_data_path, raw_out, fig_filename)
                fig_out.update(out)
                fig_data.append(fig_out)
    
    refined_text = refine_text_with_pdf(text, doc)

    # TODO: merge the paragraphs if splited by pages, figures or tables

    for page_id, page_para in enumerate(refined_text):
        for para in page_para:
            for fig_sample in fig_data:
                if 'passage' not in fig_sample.keys():
                    fig_sample['passage'] = []
                if fig_sample['id'] is not None:
                    for prefix in FIGURE_PREFIX:
                        fig_index = prefix + ' ' + fig_sample['pure_id']
                        # pdb.set_trace()
                        if fig_index in para:
                            if re.search(r'{}[A-Za-z]'.format(fig_index), para, re.I) is not None or \
                            re.search(r'{}(?!\w)'.format(fig_index), para, re.I) is not None or \
                            re.search(r'{}\([A-Za-z]\)'.format(fig_index), para, re.I) is not None:
                                if fuzz.partial_ratio(para, fig_sample['caption']) < 85:
                                    fig_sample['passage'].append(para)
                                    break
            
            for tb_sample in tb_data:
                if 'passage' not in tb_sample.keys():
                    tb_sample['passage'] = []
                if tb_sample['id'] is not None:
                    for prefix in TABLE_PREFIX:
                        tb_index = prefix + ' ' + tb_sample['pure_id']
                        if tb_index in para:
                            if re.search(r'{}[A-Za-z]'.format(tb_sample['id']), para, re.I) is not None or \
                            re.search(r'{}(?!\w)'.format(tb_sample['id']), para, re.I) is not None or \
                            re.search(r'{}\([A-Za-z]\)'.format(tb_sample['id']), para, re.I) is not None:
                                if fuzz.partial_ratio(para, tb_sample['caption']) < 85:
                                    tb_sample['passage'].append(para)
                                    break

    out_sample['table'] = tb_data
    out_sample['figure'] = fig_data
    
    return out_sample

def output_data(raw_out, pdf_root_path, raw_data_path):
    with open(os.path.join(data_saved_path, f'{args.src}.txt'), 'a', encoding='utf8') as ff:
        pdf_path = os.path.join(pdf_root_path, f'{raw_out}.pdf')
        # try:
        data = make_samples(args, raw_data_path, raw_out, pdf_path)
        if data is not None:
            ff.writelines('{}\n'.format(json.dumps(data)))
        ff.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--out_root_dir', type=str, help='Folders processed by PaddleOCR')
    parser.add_argument('--pdf_root_path', type=str, help='Pdf original files')
    parser.add_argument('--data_saved_path', type=str, help='Path for saved json/txt data')
    parser.add_argument('--src', type=str, default='', help='Paper domain, such as biorxiv or medrxiv')
    
    args = parser.parse_args()
    # out_root_dir = args.out_root_dir
    # out_root_dir = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v2'

    # raw_data_path = os.path.join(out_root_dir, args.src)
    raw_data_path = args.out_root_dir
    pdf_root_path = args.pdf_root_path

    data_saved_path = args.data_saved_path
    # data_saved_path = os.path.join(data_saved_path, args.src)
    os.makedirs(data_saved_path, exist_ok=True)
    # pdf_root_path = './pdf'
    # raw_data_path = 'out'
    # raw_out = 'antibody'
    
    raw_out_lists = os.listdir(raw_data_path)
    
    pool=mp.Pool(processes=32)
    # pdb.set_trace()
    
    for _, raw_out in enumerate(raw_out_lists):
        pool.apply_async(output_data,args=(raw_out, pdf_root_path, raw_data_path))
        # output_data(raw_out, pdf_root_path, raw_data_path)
        # except:
        #     continue
    
    pool.close()
    pool.join()
    pool.terminate()
        
    
    # pdb.set_trace()
