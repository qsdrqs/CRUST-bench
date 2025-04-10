import vertexai
from vertexai.generative_models import GenerativeModel
import os
from google import genai

import datetime
from pathlib import Path
import json
from google import genai
from google.genai.types import (
    CreateBatchJobConfig,
    CreateCachedContentConfig,
    EmbedContentConfig,
    FunctionDeclaration,
    GenerateContentConfig,
    Part,
    SafetySetting,
    Tool,
)
import multiprocessing

vertexai.init(project, location)

PROJECT_ID = "<PROJECT ID>"  # @param {type: "string", placeholder: "[your-project-id]", isTemplate: true}
if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
    PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT"))

LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "GOOGLE REGION")
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

GEMINI_CACHE = Path("../../cache/gemini_cache.jsonl")


CACHE_FLAG = True
if not os.path.exists(GEMINI_CACHE):
    with open(GEMINI_CACHE, "w", encoding="utf-8") as f:
        pass

with open(GEMINI_CACHE, "r", encoding="utf-8") as file:
    data = file.readlines()

CACHE = {json.loads(line)["prompt"]: json.loads(line) for line in data}


def call_gemini(messages, config):
    # TODO: Check the message content before sending to the model
    model_config = GenerateContentConfig(
        system_instruction=messages[0]["content"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        frequency_penalty=config["frequency_penalty"],
        presence_penalty=config["presence_penalty"],
    )
    response = client.models.generate_content(
        model=config["model"], contents=messages[1]["content"], config=model_config
    )
    return response


def get_result(messages, lock, config):
    if config is None:
        config_path = Path("./configs/gemini.json")
        config = json.loads(config_path.read_text())
    current_prompt = (
        "\n".join([msg["content"] for msg in messages]) + f"\n{json.dumps(config)}"
    )

    if CACHE_FLAG and current_prompt in CACHE:
        return CACHE[current_prompt]

    try:
        response = call_gemini(messages, config)
    except Exception as e:
        return {"prompt": current_prompt, "response": str(e), "usage": {}}
    # TODO: Check return params of gemini
    data = {
        "prompt": current_prompt,
        "response": response.text,
        "usage": {},
    }
    if CACHE_FLAG:
        with lock:
            with open(GEMINI_CACHE, "a", encoding="utf-8") as file:
                file.write(json.dumps(data) + "\n")
            CACHE[current_prompt] = data
    return data


def test_call_gemini():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the weather in San Francisco?"},
    ]
    lock = multiprocessing.Lock()
    data = get_result(messages, lock, None)
    print(data)


if __name__ == "__main__":
    test_call_gemini()
