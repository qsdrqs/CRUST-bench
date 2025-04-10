
cd ../../src/swe_agent_ablations

RUST_RES_DIR=$1
OUTPUT_DIR=$2
python swe_ver2.py \
    --input_path $RUST_RES_DIR \
    --output_path $OUTPUT_DIR/swe_agent_1_dollar \
    --cost_limit 1.00

python swe_ver2.py \
    --input_path  \
    --output_path $OUTPUT_DIR/swe_agent_2_dollar \
    --cost_limit 2.00

python swe_ver2.py \
    --input_path / \
    --output_path $OUTPUT_DIR/swe_agent_4_dollar \
    --cost_limit 4.00
