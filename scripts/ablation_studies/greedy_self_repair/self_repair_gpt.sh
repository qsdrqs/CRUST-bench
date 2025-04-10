c_dir=$1
o_dir=$2
r_dir=$3

cd ../../../src
python run.py \
        --benchmark_dir "$c_dir" \
        --output_dir "$o_dir" \
        --prompt ./prompts/transpilation_prompts/bullet_point/bullet_point_interface.prompt \
        --prompt_format bullet_point_with_system_instructions \
        --prompt_strategy all \
        --repairer_prompt ./prompts/repair_prompts/bullet_point/bullet_point.prompt \
        --repairer_format bullet_point_with_system_instructions \
        --repairer_strategy all \
        --iterations 5 \
        --mode test_normal \
        --endpoint "gpt-4o" \
        --rust_dir "$r_dir" \
        --n 1