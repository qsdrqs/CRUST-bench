import os
import json
from pathlib import Path
import re
from benchmark import Benchmark
from utils.parse_rust import function_signture_builder
from prompters.repair import (
    MarkdownRepairPrompter,
    BulletPointRepairPrompter,
)
from prompters.transpile import (
    MarkdownPrompter,
    BulletPointPrompter,
)
from prompters.test_repair import TestRepairPrompterInternal
from prompters.prompter_utils import find_best_parser

class Prompter:
    def __init__(
        self, system_prompt_path, format_style, prompting_strategy, include_headers
    ):
        self.system_prompt_path = Path(system_prompt_path)
        self.format_style = format_style
        self.prompting_strategy = prompting_strategy
        self.include_headers = include_headers

    def __call__(self, benchmark):
        if 'markdown' in self.format_style:
            if self.format_style == 'markdown':
                reminder = None
            elif self.format_style == 'markdown_with_reminder':
                reminder = 'format_reminder'
            elif self.format_style == 'markdown_with_system_instructions':
                reminder = 'format_reminder'
            else:
                raise NotImplementedError("Format style not implemented")

            if self.prompting_strategy == 'all':
                if reminder:
                    prompter = MarkdownPrompter(
                        self.system_prompt_path, self.include_headers, reminder
                    )
                else:
                    prompter = MarkdownPrompter(
                        self.system_prompt_path, self.include_headers
                    )
                prompt = prompter.build_prompt(benchmark)
                return prompt
            else:
                raise NotImplementedError("Prompting strategy not implemented")
        elif 'bullet_point' in self.format_style:
            if self.format_style == 'bullet_point':
                reminder = None
            elif self.format_style == 'bullet_point_with_reminder':
                reminder = 'format_reminder'
            elif self.format_style == 'bullet_point_with_system_instructions':
                reminder = 'rule_reminder'
            else:
                raise NotImplementedError("Format style not implemented")
            
            if self.prompting_strategy == "all":
                if reminder:
                    prompter = BulletPointPrompter(
                        self.system_prompt_path, self.include_headers, reminder
                    )
                else:
                    prompter = BulletPointPrompter(
                        self.system_prompt_path, self.include_headers
                    )
                prompts = prompter.build_prompt(benchmark)
                return prompts
            else:
                raise NotImplementedError("Prompting strategy not implemented")
            
        else:
            raise NotImplementedError("Format style not implemented")
            


    def parse_response(self, response):
        if 'markdown' in self.format_style:
            prompter = MarkdownPrompter(self.system_prompt_path, self.include_headers)
            return prompter.parse_response(response)
        elif 'bullet_point' in self.format_style:
            prompter = BulletPointPrompter(self.system_prompt_path, self.include_headers)
            return prompter.parse_response(response)
        else:
            raise NotImplementedError("Format style not implemented")

class TestRepairPrompter:
    def __init__(self, system_prompt_path, format_style, prompting_strategy):
        self.system_prompt_path = Path(system_prompt_path)
        self.format_style = format_style
        self.prompting_strategy = prompting_strategy
    def __call__(self, benchmark, iteration):
        prompter = TestRepairPrompterInternal(self.system_prompt_path)
        prompt = prompter.build_prompt(benchmark, iteration)
        return prompt
    def parse_response(self, response):
        return find_best_parser(response)
    
class RepairPrompter:
    def __init__(self, system_prompt_path, format_style, prompting_strategy):
        self.system_prompt_path = Path(system_prompt_path)
        self.format_style = format_style
        self.prompting_strategy = prompting_strategy

    def __call__(self, benchmark, iteration):
        if 'markdown' in self.format_style:
            if self.format_style == 'markdown':
                reminder = None
            elif self.format_style == 'markdown_with_reminder':
                reminder = 'format_reminder'
            elif self.format_style == 'markdown_with_system_instructions':
                reminder = 'format_reminder'
            elif self.format_style == 'graph':
                reminder = None
            else:
                raise NotImplementedError("Format style not implemented")

            if self.prompting_strategy == 'all':
                if reminder:
                    prompter = MarkdownRepairPrompter(
                        self.system_prompt_path, reminder
                    )
                else:
                    prompter = MarkdownRepairPrompter(self.system_prompt_path)
                prompt = prompter.build_prompt(benchmark, iteration)
                return prompt
            else:
                raise NotImplementedError("Prompting strategy not implemented")
        elif 'bullet_point' in self.format_style:
            if self.format_style == 'bullet_point':
                reminder = None
            elif self.format_style == 'bullet_point_with_reminder':
                reminder = 'format_reminder'
            elif self.format_style == 'bullet_point_with_system_instructions':
                reminder = 'rule_reminder'
            else:
                raise NotImplementedError("Format style not implemented")

            if self.prompting_strategy == "all":
                if reminder:
                    prompter = BulletPointRepairPrompter(
                        self.system_prompt_path, reminder
                    )
                else:
                    prompter = BulletPointRepairPrompter(self.system_prompt_path)
                prompt = prompter.build_prompt(benchmark, iteration)
                return prompt
            else:
                raise NotImplementedError("Prompting strategy not implemented")
        elif 'graph' in self.format_style:
            reminder = None
            prompter = GraphRepairPrompter(
                self.system_prompt_path, reminder
            )
            prompt = prompter.build_prompt(benchmark, iteration)
            return prompt
        else:
            raise NotImplementedError("Format style not implemented")

    def parse_response(self, response):
        if 'markdown' in self.format_style:
            prompter = MarkdownRepairPrompter(self.system_prompt_path)
            return prompter.parse_response(response)
        elif 'bullet_point' in self.format_style:
            prompter = BulletPointRepairPrompter(self.system_prompt_path)
            return prompter.parse_response(response)
        else:
            raise NotImplementedError("Format style not implemented")


if __name__ == "__main__":
    pass
