DOMAIN=debug
# PADDLE_OUT_DIR='/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v2'
# PDF_ROOT_PATH='/home/v-jiachlin/blob2/sptdata/paper_collection/saved_pdf'
# PADDLE_OUT_DIR=/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v3
# PADDLE_OUT_DIR='out_test/raw_v2'
PADDLE_OUT_DIR=out_debug
PDF_ROOT_PATH=pdf_test
# PDF_ROOT_PATH=/home/v-jiachlin/blob2/sptdata/paper_collection/saved_pdf/medrxiv

DATA_SAVED_PATH=saved_data/raw/$DOMAIN

python match_text.py \
    --src $DOMAIN \
    --out_root_dir $PADDLE_OUT_DIR \
    --pdf_root_path $PDF_ROOT_PATH \
    --data_saved_path $DATA_SAVED_PATH   