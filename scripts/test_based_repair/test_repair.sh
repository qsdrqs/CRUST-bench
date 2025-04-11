cd ../../src 

echo "Please select the model you want to run. Select the name in the brackets."
echo "1. Claude 3.5 (claude)"
echo "2. Claude 3.7 (claude37)"
echo "3. GPT-4 (gpt-4o)"
echo "4. OpenAI o1 (o1)"
echo "5. OpenAI o1-mini (o1-mini)"
echo "6. Gemini 1.5 Pro (gemini)"
echo "Please ensure for the following models you have VLLM running in the background."
echo "7. QwQ 32B (qwq)"
echo "8. Virtuoso 32B (virtuoso)"
echo "9. LLama 3 8b (llama)"

read -p "Enter your choice (please provide the name in brackets): " model
read -p "Enter the number of iterations (e.g., 5): " iterations
read -p "Enter the result directory (e.g., ../../results/claude): " res_dir
read -p "Enter the output directory (e.g., ../../results/claude): " output_dir

res_output="../results/$endpoint/repaired_tests/$model_$iterations"

python find_projects_that_build.py \
    --res_dir $res_dir \
    --output $output


python repair_tests.py \
    --input_path $output \
    --output_path $res_output \
    --endpoint $endpoint \
    --iterations $iterations

python understand_errors.py \
    --input_path $res_output
