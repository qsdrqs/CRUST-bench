cd /mnt/nas/anirudh/C_to_Rust/scripts

 


models=("o1" "o1-mini" "claude" "claude37" "gemini" "gpt-4o" "QwQ-32B-Preview" "Virtuoso-Medium-v2")
path="/mnt/nas/anirudh/results"
for model in "${models[@]}" 
do
    echo "Plotting $model"
    python determine_unresolved.py --input_path "$path/$model/test_normal/single"
    python determine_unresolved.py --input_path "$path/$model/test_normal/repair"
done