
echo "Running SWE agent 
cd ../../src/swe_agent_ablations

echo "Running SWE agent with a cost limit"
read -p "Enter the cost limit (e.g., 1.00): " cost_limit

read -p "Enter the Rust result directory (e.g., ../../results/claude37): " RUST_RES_DIR
read -p "Enter the output directory (e.g., ../../results/swe_agent): " OUTPUT_DIR

python swe_ver2.py \
    --input_path $RUST_RES_DIR \
    --output_path $OUTPUT_DIR/swe_agent_1_dollar \
    --cost_limit $cost_limit 
