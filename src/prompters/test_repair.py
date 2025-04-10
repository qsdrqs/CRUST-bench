from prompters.prompter_utils import find_best_parser
import json
class TestRepairPrompterInternal:
    def __init__(self, system_prompt_path):
        self.system_prompt_path = system_prompt_path
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    def build_prompt(self, benchmark, iteration):
        prompt = [
            {"role": "system", "content": self.system_prompt},
        ]
        final_raw_code = "You are provided with the following Rust source files:\n"
        for rust_file in benchmark.rust_files:
            file_name = rust_file["file_name"]
            content = rust_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
            final_raw_code += raw_code
        final_raw_code += "You are also provided with the Rust test files:\n"
        for rust_file in benchmark.rust_tests:
            file_name = rust_file["file_name"]
            content = rust_file["content"]
            raw_code = f"{{{{{file_name}}}}}\n```rust\n{content}```\n\n"
            final_raw_code += raw_code
        final_raw_code += "After running the tests, the following stats were found:\n"
        with open(benchmark.rust_path / "metadata" / f"test_run_{iteration}.json", "r", encoding="utf-8") as f:
            final_raw_code += f.read()
        final_raw_code += """
Reminder for Repairing Rust Code:
I need you to repair the provided Rust files, with the following instructions that you MUST follow:
- You MUST address each test failure by reasoning about it.
- Each test failure MUST be addressed by using safe Rust code.
- Do not change the test files, only correct the Rust source files.
- The corrected Rust code MUST compile and run successfully.
- The corrected Rust code MUST NOT contain Foreign Function Interface calls, such as the libc library.
- Always produce the entire file with the corrected Rust code.
Please think step-by-step and return your final solution for each corrected Rust file in the following format:

{{filename.rs}} 
```rust
// Generated Rust Code
```
"""
        prompt.append({"role": "user", "content": final_raw_code})
        prompts = [prompt]
        return prompts

    def parse_response(self, response):
        return find_best_parser(response)

