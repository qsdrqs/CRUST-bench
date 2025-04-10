import json
from pathlib import Path

CONFIG_PATH = Path("./endpoints/configs")


def endpoint_resolver(config, endpoint):
    if config != None:
        config = json.load(open(config))
    else:
        if endpoint == "claude":
            config = json.loads((CONFIG_PATH / "claude.json").read_text())
        elif endpoint == "claude37":
            config = json.loads((CONFIG_PATH / "claude37.json").read_text())
        elif endpoint == "gpt-4o":
            config = json.loads((CONFIG_PATH / "gpt_4o.json").read_text())
        elif endpoint == "o1":
            config = json.loads((CONFIG_PATH / "o1.json").read_text())
        elif endpoint == "o1-mini":
            config = json.loads((CONFIG_PATH / "o1_mini.json").read_text())
        elif endpoint == "qwq":
            config = None
        elif endpoint == "gemini":
            config = json.loads((CONFIG_PATH / "gemini.json").read_text())
        else:
            raise ValueError("Endpoint not supported")
    return config
