from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import os
import json
import multiprocessing


class QwQ:
    def __init__(self):

        self.CACHE_FILE = Path("../../cache/qwq_cache.jsonl")
        model_name = "Qwen/QwQ-32B-Preview"

        self.MODEL = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype="auto", device_map="auto"
        )
        self.TOKENIZER = AutoTokenizer.from_pretrained(model_name)

        # Turn this off only when necessary
        self.CACHE_FLAG = True
        if not os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, "w") as file:
                pass
        with open(self.CACHE_FILE, "r", encoding="utf-8") as file:
            data = file.readlines()
        self.CACHE = {json.loads(line)["prompt"]: json.loads(line) for line in data}

    def call_qwq(self, messages):

        text = self.TOKENIZER.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        model_inputs = self.TOKENIZER([text], return_tensors="pt").to(self.MODEL.device)
        generated_ids = self.MODEL.generate(**model_inputs, max_new_tokens=512)
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.TOKENIZER.batch_decode(generated_ids, skip_special_tokens=True)
        return response[0]

    def get_result(self, messages, lock, config):
        if config is None:
            pass
            # print("config wont considered for now")
        current_prompt = (
            "\n".join([msg["content"] for msg in messages]) + f"\n{json.dumps(config)}"
        )

        if self.CACHE_FLAG and current_prompt in self.CACHE:
            return self.CACHE[current_prompt]

        try:
            response = self.call_qwq(messages, config)
        except Exception as e:
            return {"prompt": current_prompt, "response": str(e), "usage": {}}
        data = {
            "prompt": current_prompt,
            "response": response,
        }
        if self.CACHE_FLAG:
            with lock:
                with open(self.CACHE_FILE, "a", encoding="utf-8") as file:
                    file.write(json.dumps(data) + "\n")
                self.CACHE[current_prompt] = data
        return data


def test_call_qwq():
    qwq = QwQ()
    lock = multiprocessing.Lock()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the weather in San Francisco in summer?"},
    ]
    data = qwq.get_result(messages, lock, None)
    print(data)


if __name__ == "__main__":
    test_call_qwq()
