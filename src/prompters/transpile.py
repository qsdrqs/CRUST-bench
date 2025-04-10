from prompters.prompter_utils import find_best_parser
import json
from pathlib import Path

class MarkdownPrompter:
    def __init__(self, system_prompt_path, include_headers, reminder='rule_reminder'):
        self.system_prompt_path = system_prompt_path
        self.include_headers = include_headers
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        if reminder == 'rule_reminder' or reminder == 'format_reminder':
            with open(Path(system_prompt_path.parent / (reminder + '.prompt')), "r", encoding="utf-8") as f:
                self.reminder = f.read()
        else:
            self.reminder = ""

    def build_prompt(self, benchmark):
        prompt = [
            {"role": "system", "content": self.system_prompt},
        ]
        final_raw_code = ""

        final_raw_code += "## The C Source Files are:\n"
        for c_file in benchmark.c_files:
            file_name = c_file["file_name"]
            content = c_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```c\n{content}```\n\n"
            final_raw_code += raw_code
        if self.include_headers:
            final_raw_code += "## The Rust Interface Files are:\n"
            for header_data in benchmark.rust_headers:
                file_name = header_data["file_name"]
                content = header_data["content"]
                raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
                final_raw_code += raw_code
        if self.reminder:
            final_raw_code += self.reminder
        prompt.append({"role": "user", "content": final_raw_code})
        prompts = [prompt]
        return prompts

    def parse_response(self, response):
        return find_best_parser(response)


class BulletPointPrompter:
    def __init__(self, system_prompt_path, include_headers, reminder='rule_reminder'):
        self.system_prompt_path = system_prompt_path
        self.include_headers = include_headers
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        if reminder == 'rule_reminder' or reminder == 'format_reminder':
            with open(Path(system_prompt_path.parent / (reminder + '.prompt')), "r", encoding="utf-8") as f:
                self.reminder = f.read()
        else:
            self.reminder = ""

    def build_prompt(self, benchmark):
        prompt = [
            {"role": "system", "content": self.system_prompt},
        ]
        final_raw_code = ""

        final_raw_code += "The C Source Files\n"
        for c_file in benchmark.c_files:
            file_name = c_file["file_name"]
            content = c_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```c\n{content}```\n\n"
            final_raw_code += raw_code
        if self.include_headers:
            final_raw_code += "The Rust Interface Files are:\n"
            for header_data in benchmark.rust_headers:
                file_name = header_data["file_name"]
                content = header_data["content"]
                raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
                final_raw_code += raw_code
        if self.reminder:
            final_raw_code += self.reminder
        prompt.append({"role": "user", "content": final_raw_code})
        prompts = [prompt]
        return prompts

    def parse_response(self, response):
        return find_best_parser(response)


