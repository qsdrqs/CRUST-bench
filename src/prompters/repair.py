from prompters.prompter_utils import find_best_parser
import json
import re

class MarkdownRepairPrompter:
    def __init__(self, system_prompt_path, reminder='rule_reminder'):
        self.system_prompt_path = system_prompt_path
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        if reminder == 'rule_reminder' or reminder == 'format_reminder':
            with open(system_prompt_path.parent / (reminder + '.prompt'), "r", encoding="utf-8") as f:
                self.reminder = f.read()
        else:
            self.reminder = ""

    def build_prompt(self, benchmark, iteration):
        prompt = [
            {"role": "system", "content": self.system_prompt},
        ]
        final_raw_code = ""
        for rust_file in benchmark.rust_files:
            file_name = rust_file["file_name"]
            content = rust_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
            final_raw_code += raw_code
        ## Errors:
        final_raw_code += "## Errors:\n"
        with open(
            benchmark.rust_path / "metadata" / f"errors_{iteration}.json",
            "r",
            encoding="utf-8",
        ) as f:
            errors = json.load(f)
        for e in errors:
            final_raw_code += f"{e['error_code']}: {e['error_message']} in {e['file_path']}:[{e['row']}:{e['col']}]\n{e['error_snippet']}\n\n"
        if self.reminder:
            final_raw_code += self.reminder
        prompt.append({"role": "user", "content": final_raw_code})
        prompts = [prompt]
        return prompts

    def parse_response(self, response):
        results = []
        raw_result_file_names_regex = re.compile(r"\{\{(.+?)\}\}\n*```")

        raw_result_file_names = raw_result_file_names_regex.findall(response)
        processed_raw_file_names = []
        for f in raw_result_file_names:
            if f.endswith(".rs"):
                processed_raw_file_names.append(f)
            else:
                processed_raw_file_names.append(f + ".rs")
        raw_result_code_regex = re.compile(r"\{\{.+?\}\}[\n]*```rust\n*([\s\S]+?)```")
        raw_result_code = raw_result_code_regex.findall(response)
        if len(processed_raw_file_names) != len(raw_result_code):
            if len(raw_result_code) > len(processed_raw_file_names):
                raw_result_code = raw_result_code[-len(processed_raw_file_names) :]
            return []
        for i in range(len(processed_raw_file_names)):
            results.append(
                {
                    "file_name": processed_raw_file_names[i],
                    "content": raw_result_code[i],
                }
            )
        return results



class BulletPointRepairPrompter:
    def __init__(self, system_prompt_path, reminder='rule_reminder'):
        self.system_prompt_path = system_prompt_path
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        if reminder == 'rule_reminder' or reminder == 'format_reminder':
            with open(system_prompt_path.parent / (reminder + '.prompt'), "r", encoding="utf-8") as f:
                self.reminder = f.read()
        else:
            self.reminder = ""

    def build_prompt(self, benchmark, iteration):
        prompt = [
            {"role": "system", "content": self.system_prompt},
        ]
        final_raw_code = ""
        for rust_file in benchmark.rust_files:
            file_name = rust_file["file_name"]
            content = rust_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
            final_raw_code += raw_code
        final_raw_code += "Errors found in the code:\n"
        with open(
            benchmark.rust_path / "metadata" / f"errors_{iteration}.json",
            "r",
            encoding="utf-8",
        ) as f:
            errors = json.load(f)
        for e in errors:
            final_raw_code += f"{e['error_code']}: {e['error_message']} in {e['file_path']}:[{e['row']}:{e['col']}]\n{e['error_snippet']}\n\n"
        if self.reminder:
            final_raw_code += self.reminder
        prompt.append({"role": "user", "content": final_raw_code})
        prompts = [prompt]
        return prompts

    def parse_response(self, response):
        return find_best_parser(response)