import os
import threading
import argparse
from tqdm import tqdm
from pps import PdfPaddleOCR
import glob
from time import ctime
import pdb

parser = argparse.ArgumentParser()
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

args = parser.parse_args()

print(f'domain: {args.src}')

raw_domain_dir = args.out_root_dir
os.makedirs(raw_domain_dir, exist_ok=True)
curr_file_list = os.listdir(raw_domain_dir)

paper_list_dir = args.paper_list_filepath


if args.filtered:
    # paper_list_dir = '/home/v-jiachlin/blob2/v-jiaclin/code/chemext/list_have_table'
    # paper_list_dir = os.path.join(paper_list_dir, args.src + '_xml', 'paper_list.txt')
    with open(paper_list_dir, 'r', encoding='utf8') as f:
        paper_list = f.readlines()
        # pdb.set_trace()
        paper_list = [item.rstrip() for item in paper_list]
        f.close()
else:
    paper_list = glob.glob(os.path.join(paper_list_dir, '*.pdf'))

# pdb.set_trace()

index_set = [0]
for i in range(args.n_jobs):
    if i == args.n_jobs - 1:
        index_set.append(len(paper_list))
    else:
        index_set.append(len(paper_list) // args.n_jobs * (i + 1))

# '/blob2/v-jiaclin/code/chemext/antibody.pdf', 'structure', 'out'
ppocr = PdfPaddleOCR()

threadLock = threading.Lock()
threads = []

def make_samples(paper_path, ppocr):
    paper_id = '.'.join(paper_path.split('/')[-1].split('.')[0:-1])
    if paper_id in curr_file_list:
        return None

    ppocr.reset(paper_path, 'structure', raw_domain_dir)
    data = ppocr.run()
    data['src'] = args.src
    data['paper_id'] = paper_id
    data['pdf_path'] = paper_path

    return data

def process_data(name, s, e):
    ppocr = PdfPaddleOCR()
    # with open(os.path.join(json_saved_dir, f'{args.src}_{name}.txt'), 'a', encoding='utf8') as ff:
    for paper_path in paper_list[s:e]:
        # pdb.set_trace()
        try:
            data = make_samples(paper_path, ppocr)
            # if data is not None:
                # ff.writelines('{}\n'.format(json.dumps(data)))
        except Exception as e:
            print(repr(e))
            continue

class myThread(threading.Thread):

    def __init__(self, threadID, name, s, e):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.s = s
        self.e = e
    
    def run(self):
        print('Starting '+ self.name + ctime(), end="")
        print(f'From {self.s} to {self.e}')
        process_data(self.name, self.s, self.e)

# process_data('', 0, 1)

for i in range(args.n_jobs):
    thread = myThread(i, f'Thread-{i}', index_set[i], index_set[i + 1])
    threads.append(thread)

for i in range(args.n_jobs):
    threads[i].start()

for t in threads:
    t.join()











    
