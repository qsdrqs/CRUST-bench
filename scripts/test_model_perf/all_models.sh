cd ../../src
cdir=$1
rdir=$2
odir=$3

for model in "gpt-4o" "o1" "o1-mini" "claude"
do
    for config in "test_seg" "test_normal"
    do
        
        python run.py \
            --benchmark_dir "$cdir" \
            --output_dir "$odir/$model/$config/bullet_point_with_system_instructions" \
            --prompt ./prompts/transpilation_prompts/bullet_point/bullet_point_interface.prompt \
            --prompt_format bullet_point_with_system_instructions \
            --prompt_strategy all \
            --repairer_prompt ./prompts/repair_prompts/bullet_point/bullet_point.prompt \
            --repairer_format bullet_point_with_system_instructions \
            --repairer_strategy all \
            --iterations 5 \
            --mode $config \
            --endpoint "$model" \
            --rust_dir "$rdir"


    done
done
