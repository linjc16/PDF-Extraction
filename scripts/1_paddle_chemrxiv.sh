DOMAIN=chemrxiv
OUT_ROOT_DIR=/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/$DOMAIN
# OUT_ROOT_DIR='out_test/raw_v2'
# PDF_PATH='pdf_test'
PDF_PATH=/home/v-jiachlin/blob2/sptdata/paper_collection/chemrxiv/pdf


python ppstru_parser.py \
    --src $DOMAIN \
    --out_root_dir $OUT_ROOT_DIR \
    --paper_list_filepath $PDF_PATH \
    --n_jobs 16