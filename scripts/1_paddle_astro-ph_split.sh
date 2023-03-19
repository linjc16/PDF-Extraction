FOLD=$1
DOMAIN=astro-ph
OUT_ROOT_DIR=/home/v-jiachlin/blob2/sptdata/tab_fig_parser/raw_v4/physics/$DOMAIN
# OUT_ROOT_DIR='out_test/raw_v2'
# PDF_PATH='pdf_test'
PDF_PATH=split_list/astro-ph_list/$FOLD.txt


python ppstru_parser.py \
    --src $DOMAIN \
    --out_root_dir $OUT_ROOT_DIR \
    --paper_list_filepath $PDF_PATH \
    --n_jobs 16 \
    --filtered