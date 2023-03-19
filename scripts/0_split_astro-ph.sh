SPLIT_NUM=5
SAVE_PATH=split_list/astro-ph_list
PDF_PATH=/home/v-jiachlin/blob2/sptdata/paper_jc/saved_pdf/astro-ph


python list_split.py \
    --split_num $SPLIT_NUM \
    --save_path $SAVE_PATH \
    --pdf_path $PDF_PATH \