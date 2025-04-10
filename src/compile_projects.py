import json
import os
import sys
from pathlib import Path
from utils.compile_rust_utils import (
    compile_rust_proj,
    create_error_report,
    compile_rust_test_proj,
)
from utils.rust_project_builder import create_top_level_cargo_toml
import subprocess
from tqdm import tqdm

def run_tests(project_path):
    try:
        result = subprocess.run(
        ["cargo", "test" ], cwd=project_path, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return "Timeout", "Timeout"
    return result.stdout, result.stderr
    
        
def test(output_dir, iteration):
    res = []
    for proj in tqdm([o for o in output_dir.iterdir()]):
        if not proj.is_dir() or not "Cargo.toml" in os.listdir(proj):
            continue
        stdout, stderr = run_tests(proj)
    
        oks = stdout.count('... ok')
        fails = stdout.count('... FAILED')
        if fails != 0:
            with open(proj / "metadata" / f"test_run_{iteration}.json", "w", encoding="utf-8") as f:
                f.write(stdout)
        res.append({"project": proj.name, "ok": oks, "fail": fails})
    with open(output_dir / f"test_report_{iteration}.json", "w", encoding="utf-8") as f:
        json.dump(res, f)
    

def compile(output_dir: Path, iteration: int):
    result = []
    if not Path(output_dir / "Cargo.toml").exists():
        create_top_level_cargo_toml(output_dir)
    for proj in output_dir.iterdir():
        if not proj.is_dir() or not "Cargo.toml" in os.listdir(proj):
            continue
        result_line = {}
        result_line["iteration"] = iteration
        result_line["project"] = proj
        result_line["errors"] = 0
        if proj.is_dir():
            if "Cargo.toml" in os.listdir(proj):
                e1 = compile_rust_proj(proj)
                e2 = compile_rust_test_proj(proj)
                if e1 is not None and e2 is not None:
                    e = e1 + e2
                elif e1 is not None:
                    e = e1
                elif e2 is not None:
                    e = e2
                else:
                    e = None
                metadata_path = proj / "metadata"
                if e:
                    if not metadata_path.exists():
                        metadata_path.mkdir()
                    errors = create_error_report(e)
                    if errors != []:
                        with open(
                            metadata_path / f"errors_{iteration}.json",
                            "w",
                            encoding="utf-8",
                        ) as f:
                            json.dump(errors, f)
                        with open(
                            metadata_path / f"build_errors_{iteration}.json",
                            "w",
                            encoding="utf-8",
                        ) as f:
                            error_report_build = create_error_report(e1)
                            json.dump(error_report_build, f)
                        with open(
                            metadata_path / f"test_errors_{iteration}.json",
                            "w",
                            encoding="utf-8",
                        ) as f:
                            error_report_test = create_error_report(e2)
                            test_errors = []
                            for error in error_report_test:
                                if "bin" in error["file_path"]:
                                    test_errors.append(error)
                            json.dump(test_errors, f)

                    result_line["errors"] = len(errors)
        result.append(result_line)
    return result
