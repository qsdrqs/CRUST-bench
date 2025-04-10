# The code in this file is used to call the vLLM server.
from openai import OpenAI
from pathlib import Path
import os
import json
import multiprocessing
from openai import OpenAI

CACHE_FILE = Path("../../cache/os_model_cache.jsonl")
# Turn this off only when necessary
CACHE_FLAG = True
if not os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "w") as file:
        pass
with open(CACHE_FILE, "r", encoding="utf-8") as file:
    data = file.readlines()
CACHE = {json.loads(line)["prompt"]: json.loads(line) for line in data}


# This uses the OpenAI API to call the vLLM server.
class VLLMServer:
    def __init__(self, model_name):
        self.model_name = model_name

        # Modify OpenAI's API key and API base to use vLLM's API server.
        self.openai_api_key = "EMPTY"
        self.openai_api_base = ""
        with open(
            f"server_url_{self.model_name.split('/')[-1]}.txt", "r", encoding="utf-8"
        ) as file:
            self.openai_api_base = file.read().strip()
        self.openai_api_base += "/v1"

        self.client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=self.openai_api_key,
            base_url=self.openai_api_base,
        )

    def call_gpt(self, messages, config):
        if "temperature" in config:
            temperature = config["temperature"]
        else:
            temperature = 0.0
        messages = messages
        response = self.client.chat.completions.create(
            model=config["model"],
            messages=messages,
            temperature=temperature,
        )
        return response

    def get_result(self, messages, lock, config):
        if config is None:
            raise ValueError("Config is None. Please look into the config.")
        current_prompt = (
            "\n".join([msg["content"] for msg in messages]) + f"\n{json.dumps(config)}"
        )

        if CACHE_FLAG and current_prompt in CACHE:
            return CACHE[current_prompt]

        try:
            response = self.call_gpt(messages, config)
        except Exception as e:
            return {"prompt": current_prompt, "response": str(e), "usage": {}}
        data = {
            "prompt": current_prompt,
            "response": response.choices[0].message.content,
            "usage": {
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
        if CACHE_FLAG:
            with lock:
                with open(CACHE_FILE, "a", encoding="utf-8") as file:
                    file.write(json.dumps(data) + "\n")
                CACHE[current_prompt] = data
        return data


def test_call_gpt(server, config):
    lock = multiprocessing.Lock()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the weather in San Francisco?"},
    ]
    data = server.get_result(messages, lock, config)
    print(data)


if __name__ == "__main__":
    config1 = Path("./configs/qwq.json").read_text()
    config1 = json.loads(config1)
    server = VLLMServer("qwq")
    test_call_gpt(server, config1)
