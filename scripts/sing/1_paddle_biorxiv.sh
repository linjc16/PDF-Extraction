DOMAIN=biorxiv
OUT_ROOT_DIR=/blob2/sptdata/tab_fig_parser/raw_v4.1/$DOMAIN
# OUT_ROOT_DIR='out_test/raw_v2'
# PDF_PATH='pdf_test'
PDF_PATH=/blob2/sptdata/paper_collection/biorxiv/biorxiv

# -m torch.distributed.launch --nproc_per_node=${GPU_PER_NODE_COUNT} --node_rank=${NODE_RANK} --nnodes=${NODE_COUNT} --master_addr=${MASTER_ADDR} --master_port=${MASTER_PORT}
python ppstru_parser.py \
    --src $DOMAIN \
    --out_root_dir $OUT_ROOT_DIR \
    --paper_list_filepath $PDF_PATH \
    --n_jobs 16