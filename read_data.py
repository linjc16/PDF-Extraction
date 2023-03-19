import json
import argparse
from tqdm import tqdm
import os
import pdb

parser = argparse.ArgumentParser()
parser.add_argument('--data_path', type=str)
parser.add_argument('--domain', type=str, default='debug0317')
args = parser.parse_args()

# data_path = args.data_path
# data_path = 'saved_data/raw/medrxiv_2/medrxiv.txt'
data_path = 'saved_data/raw/chemrxiv/chemrxiv.txt'
# root_save_path = '/home/v-jiachlin/blob2/sptdata/mmspt_datasets'
root_save_path = 'saved_data/raw_v2'
version = 1

root_save_path = os.path.join(root_save_path, args.domain)
os.makedirs(root_save_path, exist_ok=True)

fig_data = []
table_data = []

with open(data_path, 'r', encoding='utf8') as f:
    samples = f.readlines()
    for sample in tqdm(samples):
        try: 
            sample = json.loads(sample)
            for tb_sample in sample['table']:
                if tb_sample['id'] is not None and len(tb_sample['passage']) > 0:
                    table_data.append(tb_sample)
            
            for fig_sample in sample['figure']:
                if fig_sample['id'] is not None and len(fig_sample['passage']) > 0:
                    fig_data.append(fig_sample)
        except Exception as e:
            print(repr(e))
            continue
    f.close()
# fig_data = [json.dumps(item, indent=4) for item in fig_data]

# with open(os.path.join(root_save_path, f'fig_{args.domain}_v{version}.json'), 'w') as f:
#     [f.writelines('{}\n'.format(json.dumps(data))) for data in fig_data]
#     f.close()
# with open(os.path.join(root_save_path, f'table_{args.domain}_v{version}.json'), 'w') as f:
#     [f.writelines('{}\n'.format(json.dumps(data))) for data in table_data]
#     f.close()

import pandas as pd

excel_path_list = []
fig_path_list = []
caption_list = []
html_list = []
passage_list = []

from data_visulization import visualize_to_excel

for data in table_data:
    excel_path_list.append(data['excel_path'])
    fig_path_list.append(data['fig_path'])
    caption_list.append(data['caption'])
    html_list.append(data['html'])
    passage_list.append('\n'.join(data['passage']))

visualize_to_excel(root_save_path, fig_path_list, caption_list, html_list, passage_list)



# tb_df = pd.DataFrame.from_dict(
#     {
#         'excel_path': excel_path_list,
#         'fig_path': fig_path_list,
#         'caption': caption_list,
#         'html': html_list,
#         'passage_list': passage_list
#     }
# )

# tb_df.to_csv(os.path.join(root_save_path, f'tb_{args.domain}_v{version}.csv'))

# pdb.set_trace()