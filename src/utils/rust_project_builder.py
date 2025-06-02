import os
import subprocess
from pathlib import Path
import json
import shutil
FILE_PATH=Path(__file__)
DEPENDENCIES_FILE = FILE_PATH.parent.parent / "resources/cache/dependencies.json"
DEPENDENCIES = {}
print(os.getcwd())
with open(DEPENDENCIES_FILE, "r") as f:
    DEPENDENCIES = json.load(f)


def create_top_level_cargo_toml(output_dir):
    members = []
    for d in os.listdir(output_dir):
        if os.path.isdir(f"{output_dir}/{d}") and "d" != "target":
            members.append(d)
    with open(f"{output_dir}/Cargo.toml", "w", encoding="utf-8") as file:
        dep = [f'{d} = "{DEPENDENCIES[d]}"' for d in DEPENDENCIES]

        members_string = ", ".join([f'"{m}"' for m in members])
        file.write(
            f'[workspace]\nmembers = [{members_string}]\nresolver="2"'
            + f"\n[workspace.dependencies]\n"
            + "\n".join(dep)
        )


def create_rust_proj(proj_name: str, cwd: Path = Path.cwd()):
    # run command cargo new proj_name
    subprocess.run(["cargo", "new", proj_name], cwd=cwd)
    return proj_name


def write_rust_test_files(benchmark):
    for res in benchmark.rust_test_files:
        output_bin_dir = benchmark.benchmark.rust_path / "src" / "bin"
        if not output_bin_dir.exists():
            output_bin_dir.mkdir(parents=True)
        with open(
            output_bin_dir / res["file_name"].split("/")[-1],
            "w",
            encoding="utf-8",
        ) as file:
            content = res["content"]
            if "pub fn main()" not in res["content"]:
                content = res["content"] + "\nfn main() {}"
            file.write(content)


def write_rust_bin_files(benchmark):
    for res in benchmark.rust_test_files:
        with open(
            benchmark.rust_path / "src" / "bin" / res["file_name"].split("/")[-1],
            "w",
            encoding="utf-8",
        ) as file:
            content = res["content"]
            if "pub fn main()" not in res["content"]:
                content = res["content"] + "\nfn main() {}"
            file.write(content)


def write_rust_interfaces(benchmark):
    if not (benchmark.rust_path / "src" / "interfaces").exists():
        (benchmark.rust_path / "src" / "interfaces").mkdir()
    for res in benchmark.rust_headers:
        with open(
            benchmark.rust_path
            / "src"
            / "interfaces"
            / res["file_name"].split("/")[-1],
            "w",
            encoding="utf-8",
        ) as file:
            file.write(res["content"])


def write_rust_files(benchmark):
    for res in benchmark.rust_files:
        if res["file_name"] == "lib.rs":
            continue
        with open(
            benchmark.rust_path / "src" / res["file_name"].split("/")[-1],
            "w",
            encoding="utf-8",
        ) as file:
            file.write(res["content"])
    with open(benchmark.rust_path / "src" / "lib.rs", "w", encoding="utf-8") as file:
        for res in benchmark.rust_files:
            if res["file_name"] != "main.rs" and res["file_name"] != "lib.rs":
                file.write(f'pub mod {res["file_name"].split(".")[0]};\n')
    
    if Path(benchmark.rust_path / "Cargo.toml").exists():
        with open(benchmark.rust_path / "Cargo.toml", "r", encoding="utf-8") as file:
            content = file.read()
        with open(benchmark.rust_path / "Cargo.toml", "w", encoding="utf-8") as file:
            for dep in DEPENDENCIES:
                if dep not in content:
                    content = content.replace(
                        "[dependencies]",
                        f"[dependencies]\n{dep} = {{ workspace = true }}\n",
                    )
            file.write(content)
    

def write_rust_multi_files(benchmark_cand, i):
    benchmark , candidate = benchmark_cand
    proj_path = Path(benchmark.rust_path.parent / f"{i}" / benchmark.rust_path.name)
    shutil.copytree(benchmark.rust_path, proj_path)
    for res in benchmark.rust_files:
        with open(
            proj_path / "src" / res["file_name"].split("/")[-1],
            "w",
            encoding="utf-8",
        ) as file:
            file.write(res["content"])
    meta_data_path = proj_path / "metadata"
    output_metadata_path = meta_data_path / "output"
    if not output_metadata_path.exists():
        output_metadata_path.mkdir(parents=True)
    with open(output_metadata_path / "initial.txt", "w", encoding="utf-8") as file:
        file.write(candidate)
    

    ######### main file written here #########
    # # read main.rs
    # with open(benchmark.rust_path / "src" / "main.rs", "r", encoding="utf-8") as file:
    #     main_content = file.read()
    # # include all files in main.rs
    # for res in benchmark.rust_files:
    #     if res["file_name"] != "main.rs":
    #         if f"mod {res['file_name'].split('.')[0]};" not in main_content:
    #             main_content = f"use {benchmark.project_name}::{res['file_name'].split('.')[0]};\n" + main_content
    # # write main.rs
    # with open(benchmark.rust_path / "src" / "main.rs", "w", encoding="utf-8") as file:
    #     file.write(main_content)
    #############################################
    with open(proj_path / "src" / "lib.rs", "w", encoding="utf-8") as file:
        for res in benchmark.rust_files:
            if res["file_name"] != "main.rs" and res["file_name"] != "lib.rs":
                file.write(f'pub mod {res["file_name"].split(".")[0]};\n')
    # cargo file since we are using workspace
    if Path(f"{proj_path}/Cargo.toml").exists():
        with open(f"{proj_path}/Cargo.toml", "r", encoding="utf-8") as file:
            content = file.read()
        with open(f"{proj_path}/Cargo.toml", "w", encoding="utf-8") as file:
            for dep in DEPENDENCIES:
                if dep not in content:
                    content = content.replace(
                        "[dependencies]",
                        f"[dependencies]\n{dep} = {{ workspace = true }}\n",
                    )
            file.write(content)

