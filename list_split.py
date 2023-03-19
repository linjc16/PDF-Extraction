import os
import json
import glob
import argparse
import pdb


parser = argparse.ArgumentParser()
parser.add_argument('--split_num', type=int)
parser.add_argument('--save_path', type=str)
parser.add_argument('--pdf_path', type=str)
parser.add_argument('--filtered', default=False, action='store_true', help='Using the txt files containing pdf filename list')

args = parser.parse_args()

pdf_path = args.pdf_path

if args.filtered:
    # paper_list_dir = '/home/v-jiachlin/blob2/v-jiaclin/code/chemext/list_have_table'
    # paper_list_dir = os.path.join(paper_list_dir, args.src + '_xml', 'paper_list.txt')
    with open(pdf_path, 'r', encoding='utf8') as f:
        pdf_list = f.readlines()
        # pdb.set_trace()
        pdf_list = [item.rstrip() for item in pdf_list]
        pdf_list = list(filter(None, pdf_list))
        f.close()
else:
    pdf_list = glob.glob(os.path.join(pdf_path, '*.pdf'))
# pdf_path = '/home/v-jiachlin/blob2/sptdata/paper_collection/biorxiv/biorxiv'
# save_path = 'biorxiv_list'


save_path = args.save_path

os.makedirs(save_path, exist_ok=True)

# pdf_list = glob.glob(os.path.join(pdf_path, '*.pdf'))

index_set = [0]
for i in range(args.split_num):
    if i == args.split_num - 1:
        index_set.append(len(pdf_list))
    else:
        index_set.append(len(pdf_list) // args.split_num * (i + 1))

# pdb.set_trace()

for i in range(args.split_num):
    with open(os.path.join(save_path, f'{i}.txt'), 'w', encoding='utf8') as f:
        data = pdf_list[index_set[i]:index_set[i + 1]]
        f.writelines('{}'.format('\n'.join(data)))
        
        f.close()