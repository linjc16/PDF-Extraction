import glob
import json
import pdb
import os
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument('--src', type=str, default='') # biorxiv, medrxiv
# args = parser.parse_args()

# file_lists = glob.glob(f'/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw/{args.src}*.txt')

# saved_raw_filepath = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v3'
# saved_raw_filepath = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/chemrxiv'
# saved_raw_filepath = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/biorxiv'
saved_raw_filepath = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/material'
# saved_raw_filepath = '/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/physics/astro-ph'
curr_file_list = os.listdir(os.path.join(saved_raw_filepath))


# count = 0

# for filename in file_lists:
#     with open (filename, 'r', encoding='utf8') as f:
#         temp = f.readlines()
#         # pdb.set_trace()
#         # data = json.loads(temp)
#         count += len(temp)
#         # pdb.set_trace()
#         f.close()

print(f'Totally {len(curr_file_list)} data.')
