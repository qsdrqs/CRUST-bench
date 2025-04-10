import os
import vertexai


class KeyHandler:
    key = "<OPENAI KEY>"
    claude_key = "<CLAUDE KEY>"
    hf_key = "<HF KEY>"
    google_project_id = "<GOOGLE PROJECT ID>"
    google_project_location = "<GOOGLE PROJECT LOCATION>"

    @classmethod
    def set_env_key(cls):
        from src.utils.paths import ROOT_FOLDER

        os.environ["HF_API_KEY"] = cls.hf_key
