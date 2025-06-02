import json
import os
from pathlib import Path
from utils.compile_c_utils import build_c_project
from utils.rust_project_builder import create_rust_proj, create_top_level_cargo_toml
from utils.compile_rust_utils import compile_rust_proj, create_error_report
from utils.parse_c import get_header_files
import re
import subprocess


def remove_comments(code):
    # Remove all single-line comments (//)
    code = re.sub(r"//.*?\n", "\n", code)

    # Remove all multi-line comments (/* */)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)

    # replace the multiple \n with single \n
    code = re.sub(r"\n+", "\n", code)

    return code


def load_benchmarks(input_dir, output_dir):
    benchmarks = []
    print(f"Loading benchmarks from {input_dir}")
    for proj in os.listdir(input_dir):
        if not os.path.isdir(f"{input_dir}/{proj}"):
            continue
        benchmarks.append(Benchmark(f"{input_dir}/{proj}", f"{output_dir}/{proj}"))
    print(f"Loaded {len(benchmarks)} benchmarks")
    return benchmarks


class Benchmark:
    def __init__(self, c_path, rust_path):
        self.c_path = Path(c_path)

        self.project_name = self.c_path.name.replace("-", "_")
        if self.project_name[0].isdigit():
            self.project_name = "proj_" + self.project_name
        if len(self.project_name.split(".")) > 1:
            self.project_name = self.project_name.split(".")[0]
        
        self.rust_path = Path(rust_path).parent / self.project_name
        self.c_files = self.get_c_files()
        self.c_headers = get_header_files(self)
        if not self.rust_path.parent.exists():
            self.rust_path.parent.mkdir(parents=True, exist_ok=True)
        self.rust_files = []
        self.rust_headers = []
        self.rust_tests = []
        if not self.rust_path.exists():
            create_rust_proj(self.project_name, self.rust_path.parent)
            with open(
                self.rust_path / "src" / "main.rs", "r", encoding="utf-8"
            ) as file:
                self.rust_files.append(
                    {
                        "file_name": "main.rs",
                        "content": file.read(),
                    }
                )
        else:
            for file_path in Path(self.rust_path / "src").iterdir():
                if file_path.is_dir() or not file_path.name.endswith(".rs"):
                    continue
                with open(file_path, "r", encoding="utf-8") as file:
                    self.rust_files.append(
                        {
                            "file_name": Path(file_path).stem + Path(file_path).suffix,
                            "content": remove_comments(file.read()),
                        }
                    )
            for file_path in self.rust_path.rglob("src/interfaces/*.rs"):
                if file_path.is_dir():
                    continue
                with open(file_path, "r", encoding="utf-8") as file:
                    self.rust_headers.append(
                        {
                            "file_name": Path(file_path).stem + Path(file_path).suffix,
                            "content": file.read(),
                        }
                    )
            for file_path in self.rust_path.rglob("src/bin/*.rs"):
                if file_path.is_dir():
                    continue
                with open(file_path, "r", encoding="utf-8") as file:
                    self.rust_tests.append(
                        {
                            "file_name": Path(file_path).stem + Path(file_path).suffix,
                            "content": file.read(),
                        }
                    )
        assert self.c_files, "No C files found in the benchmark: " + str(c_path)
        # sort the c files
        self.c_files = sorted(self.c_files, key=lambda x: x["file_name"])
        self.rust_files = sorted(self.rust_files, key=lambda x: x["file_name"])
        self.rust_headers = sorted(self.rust_headers, key=lambda x: x["file_name"])
        self.c_headers = sorted(self.c_headers, key=lambda x: x["file_name"])
        


    def process_c_and_h_files(self):
        c_files = []
        changed = []
        visited = set()
        c_dict = {}
        for c_file in self.c_files:
            c_dict[c_file["file_name"]] = c_file["content"]
        reversed_c_files = sorted(
            self.c_files, reverse=True, key=lambda x: x["file_name"]
        )
        for c_file in reversed_c_files:
            if c_file["file_name"] in visited:
                continue
            c_file_name = c_file["file_name"]
            c_file_content = c_file["content"]
            if c_file_name.endswith(".h"):
                # check if a file with the same name exists
                if c_file_name[:-2] + ".c" in c_dict:
                    visited.add(c_file_name[:-2] + ".c")
                    c_files.append(
                        {
                            "file_name": c_file_name[:-2] + ".c",
                            "content": "// header file\n/*"
                            + c_file_content
                            + "*/\n"
                            + c_dict[c_file_name[:-2] + ".c"],
                        }
                    )
                    changed.append(c_file_name)
                else:
                    c_files.append(c_file)
            else:
                c_files.append(c_file)
        # update namings
        for changed_file in changed:
            for c_file in c_files:
                if changed_file in c_file["content"]:
                    if changed_file.split(".")[0] == c_file["file_name"].split(".")[0]:
                        continue
                    else:
                        c_file["content"] = c_file["content"].replace(
                            changed_file, changed_file[:-2] + ".c"
                        )
        c_files = sorted(c_files, key=lambda x: x["file_name"])
        self.c_files = c_files
        return c_files

    def get_c_files(self):
        c_files = []
        for files in self.c_path.rglob("**/*"):
            if files.is_dir():
                continue
            if (
                (str(files).endswith(".c") or str(files).endswith(".h"))
                and "test" not in str(files)
                and "tests" not in str(files)
                and "example" not in str(files)
                and "examples" not in str(files)
                and "benchmark" not in str(files)
                and "bin" not in str(files.parent)
                and "unity" not in str(files)
                and 'CMakeCCompilerId' not in str(files)
            ):
                with open(files, "r", encoding="utf-8", errors="ignore") as file:
                    c_files.append(
                        {
                            "file_name": str(files.stem) + str(files.suffix),
                            "content": remove_comments(file.read()),
                        }
                    )
        return c_files

    def compile_c(self):
        return build_c_project(self.c_path)

    def compile_rust(self):
        e = compile_rust_proj(self.rust_path)
        if e:
            errors = create_error_report(e)
            return errors
        return None

    def count_loc(self):
        c_loc = 0
        for file in self.c_files:
            comments_removed = remove_comments(file["content"])
            c_loc += sum(1 for line in comments_removed.split("\n") if line.strip())
        rust_loc = 0
        for file in self.rust_files:
            comments_removed = remove_comments(file["content"])
            rust_loc += sum(1 for line in comments_removed.split("\n") if line.strip())
        return c_loc, rust_loc


if __name__ == "__main__":
    c_path = Path(__file__).parent.parent / 'datasets/CBench'
    rust_path = Path(__file__).parent.parent / 'datasets/RBench'
    for proj in os.listdir(c_path):
        b = Benchmark(f"{c_path}/{proj}", f"{rust_path}")
    print("successfully created benchmarks")
    subprocess.run(["rm", "-rf", f"{rust_path}"])
