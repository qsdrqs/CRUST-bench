datapath="/mnt/nas/anirudh/datasets/raw/github_pt2_small"
cluster=$1
outputpath="/mnt/nas/anirudh/C_to_Rust/results"
promptpath="/mnt/nas/anirudh/C_to_Rust/scripts/prompts/safe_rust_ffi/transpilation_prompts"
repairpath="/mnt/nas/anirudh/C_to_Rust/scripts/prompts/safe_rust_ffi/repair_prompts"



python run.py --benchmark_dir $datapath --output_dir $outputpath/markdown/safe_rust_ffi_system_sys_reminder/github_ver2 --prompt $promptpath/markdown/safe_rust_ffi_system.prompt --prompt_format markdown_with_system_instructions --prompt_strategy all --repairer_prompt $repairpath/markdown/safe_rust_ffi_repair_system.prompt --repairer_format markdown_with_system_instructions --repairer_strategy all --iterations 5

