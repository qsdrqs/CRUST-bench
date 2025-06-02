import anthropic
from pathlib import Path
import os
import json
import multiprocessing

FILE_PATH = Path(__file__)
CLAUDE_CACHE = FILE_PATH.parent /"cache/claude_cache.jsonl"
if not CLAUDE_CACHE.parent.exists():
    CLAUDE_CACHE.parent.mkdir(parents=True, exist_ok=True)
client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
)

CACHE_FLAG = True
if not os.path.exists(CLAUDE_CACHE):
    with open(CLAUDE_CACHE, "w", encoding="utf-8") as f:
        pass

with open(CLAUDE_CACHE, "r", encoding="utf-8") as file:
    data = file.readlines()

CACHE = {json.loads(line)["prompt"]: json.loads(line) for line in data}


def call_claude(messages, config):
    # TODO: Check the message content before sending to the model
    message = client.messages.create(
        model=config["model"],
        max_tokens=config["max_tokens"],
        temperature=config["temperature"],
        system=messages[0]["content"],
        messages=messages[1:],
    )
    return message.content


def get_result(messages, lock, config):
    if config is None:
        config_path = FILE_PATH.parent/"configs/claude.json"
        config = json.loads(config_path.read_text())
    current_prompt = (
        "\n".join([msg["content"] for msg in messages]) + f"\n{json.dumps(config)}"
    )

    if CACHE_FLAG and current_prompt in CACHE:
        return CACHE[current_prompt]

    try:
        response = call_claude(messages, config)
    except Exception as e:
        return {"prompt": current_prompt, "response": str(e), "usage": {}}
    # TODO: Check return params of claude
    data = {
        "prompt": current_prompt,
        "response": response[0].text,
        "usage": {},
    }
    if CACHE_FLAG:
        if "Error code: 429" not in data["response"]:
            with lock:
                with open(CLAUDE_CACHE, "a", encoding="utf-8") as file:
                    file.write(json.dumps(data) + "\n")
                CACHE[current_prompt] = data
    return data


def get_result_n(messages, lock, config, n):
    if config is None or config["temperature"] == 0:
        raise ValueError("Config is None. Please look into the config.")
    current_prompt = (
        "\n".join([msg["content"] for msg in messages])
        + f"\n{json.dumps(config)}"
        + f"\n={n}"
    )

    if CACHE_FLAG and current_prompt in CACHE:
        return CACHE[current_prompt]

    try:
        res = []
        print("Calling claude")
        for _ in range(n):
            response = call_claude(messages, config)
            res.append(response)
    except Exception as e:
        return {"prompt": current_prompt, "response": str(e), "usage": {}}
    data = {
        "prompt": current_prompt,
        "response": [choice[0].text for choice in res],
        "usage": {},
    }
    if CACHE_FLAG:
        with lock:
            with open(CLAUDE_CACHE, "a", encoding="utf-8") as file:
                file.write(json.dumps(data) + "\n")
            CACHE[current_prompt] = data
    return data


def test_call_claude():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the weather in San Francisco?"},
    ]
    lock = multiprocessing.Lock()
    data = get_result(messages, lock)
    print(data)


if __name__ == "__main__":
    test_call_claude()
