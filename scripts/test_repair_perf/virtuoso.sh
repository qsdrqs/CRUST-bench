cd /mnt/nas/anirudh/C_to_Rust/scripts
endpoint="Virtuoso-Medium-v2"
res_dir="/mnt/nas/anirudh/results/$endpoint/test_normal/repair"
output="/mnt/nas/anirudh/repair_test_inputs/$endpoint"
res_output="/mnt/nas/anirudh/results/$endpoint/repaired_tests"
config="/mnt/nas/anirudh/C_to_Rust/scripts/endpoints/configs/deepseek_v3.json"
python find_projects_that_build.py \
    --res_dir $res_dir \
    --output $output


python repair_tests.py \
    --input_path $output \
    --output_path $res_output \
    --endpoint $endpoint \
    --config $config


python understand_errors.py --input_path $res_output
