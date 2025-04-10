cd ../../src
cdir=$1
rdir=$2
odir=$3
model="DeepSeek-R1-Distill-Qwen-32B"
model_config="./endpoints/configs/deepseek_r1_qwen.json"
config="test_normal"
        
python run.py \
    --benchmark_dir "$cdir" \
    --output_dir "$odir/$model/$config/bullet_point_with_system_instructions_repair_3" \
    --prompt ./prompts/safe_rust_ffi/transpilation_prompts/bullet_point/bullet_point_interface.prompt \
    --prompt_format bullet_point_with_system_instructions \
    --prompt_strategy all \
    --repairer_prompt ./prompts/safe_rust_ffi/repair_prompts/bullet_point/bullet_point.prompt \
    --repairer_format bullet_point_with_system_instructions \
    --repairer_strategy all \
    --iterations 3 \
    --mode $config \
    --endpoint "$model" \
    --rust_dir "$rdir" \
    --config "$model_config"
    



