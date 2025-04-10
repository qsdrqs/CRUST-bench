import json
import os
import re
from pathlib import Path
import subprocess
from typing import List
import csv
import sys
from tqdm import tqdm
ERROR_DICT_PATH = Path(
    "../resources/error_dict/error_dict.json"
)
with open(ERROR_DICT_PATH, "r", encoding="utf-8") as f:
    ERROR_DICT = json.load(f)


# main core function to compile rust project
def compile_rust_proj(proj_name):
    result = subprocess.run(
        ["cargo", "build"], cwd=proj_name, capture_output=True, text=True
    )
    std_out = result.stdout
    std_err = result.stderr
    if std_err:
        return std_err
    else:
        return None


def compile_rust_test_proj(proj_name):
    try:
        result = subprocess.run(
            ["cargo", "test"], cwd=proj_name, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return "Timeout"
    std_out = result.stdout
    std_err = result.stderr
    if 'error' not in std_err:
        return None
    
    else:
        return std_err 


def compile_all_rust_proj(dir_path: Path):
    all_errors = {}
    err_dict = {}
    for proj_path in dir_path.iterdir():
        if proj_path.is_dir():
            # print(os.listdir(proj_path))
            if "Cargo.toml" not in os.listdir(proj_path):
                continue
            e = compile_rust_proj(proj_path)
            all_errors[str(proj_path)] = e

    return all_errors, err_dict


def test_all_rust_proj(dir_path: Path):
    all_errors = {}
    err_dict = {}
    for proj_path in tqdm(list(dir_path.iterdir())):
        if proj_path.is_dir():
            # print(os.listdir(proj_path))
            if "Cargo.toml" not in os.listdir(proj_path):
                continue
            e = compile_rust_test_proj(proj_path)
            all_errors[str(proj_path)] = e

    return all_errors, err_dict


def final_test_report(dir_path: Path):
    all_errors, err_dict = test_all_rust_proj(dir_path)
    all_errors = {e: create_error_report(all_errors[e]) for e in all_errors}

    with open(dir_path / "test_report.csv", "w", newline="") as f:
        csv.writer(f).writerow(
            ["project", "error_code", "error_message", "file_path", "row", "col"]
        )
        for proj in all_errors:
            if not all_errors[proj]:
                csv.writer(f).writerow(
                    [
                        str(proj).split("/")[-1],
                        "No errors",
                        "No errors",
                        "No errors",
                        "No errors",
                        "No errors",
                    ]
                )
            for error in all_errors[proj]:
                csv.writer(f).writerow(
                    [
                        str(proj).split("/")[-1],
                        error["error_code"],
                        error["error_message"],
                        error["file_path"],
                        error["row"],
                        error["col"],
                    ]
                )


def final_error_report(dir_path: Path):
    all_errors, err_dict = compile_all_rust_proj(dir_path)
    all_errors = {e: create_error_report(all_errors[e]) for e in all_errors}

    with open(dir_path / "error_report.csv", "w", newline="") as f:
        csv.writer(f).writerow(
            ["project", "error_code", "error_message", "file_path", "row", "col"]
        )
        for proj in all_errors:
            if not all_errors[proj]:
                csv.writer(f).writerow(
                    [
                        str(proj).split("/")[-1],
                        "No errors",
                        "No errors",
                        "No errors",
                        "No errors",
                        "No errors",
                    ]
                )
            for error in all_errors[proj]:
                csv.writer(f).writerow(
                    [
                        str(proj).split("/")[-1],
                        error["error_code"],
                        error["error_message"],
                        error["file_path"],
                        error["row"],
                        error["col"],
                    ]
                )


def get_all_errors_for_project(proj_path):
    errors = []
    for file in proj_path.iterdir():
        if "errors" in file.name:
            with open(file, "r") as f:
                error = json.load(f)
                errors.append(error)
    e = compile_rust_proj(proj_path)
    errors.append(e)
    return errors


def get_errors_for_iteration(output_folder):
    error_per_proj = {}
    error_count_dict = [{}, {}, {}, {}, {}, {}]
    with open(output_folder / "error_count.csv", "w", newline="") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(
            [
                "iteration",
                "project",
                "error_code",
                "error_message",
                "file_path",
                "row",
                "col",
            ]
        )
        rows = []
        for proj in output_folder.iterdir():
            if proj.is_dir() and "Cargo.toml" in os.listdir(proj):
                error_per_proj[str(proj)] = []
                for i in range(6):
                    error_file = proj / "metadata" / f"errors_{i}.json"
                    if error_file.exists():
                        with open(error_file, "r") as f:
                            errors = json.load(f)
                            error_per_proj[str(proj)].append(errors)
                            error_count_dict[i][str(proj)] = errors
                        for e in errors:
                            rows.append(
                                [
                                    i,
                                    str(proj).split("/")[-1],
                                    e["error_code"],
                                    e["error_message"],
                                    e["file_path"],
                                    e["row"],
                                    e["col"],
                                ]
                            )
        rows = sorted(rows, key=lambda x: (x[0], x[1]))
        csv_writer.writerows(rows)


def create_error_blocks(std_err):
    blocks = []
    flag_error = False
    for x in std_err.split("\n"):
        if x.startswith("error"):
            flag_error = True
            blocks.append(x)
        elif x.startswith("warning"):
            flag_error = False
        else:
            if flag_error:
                blocks.append(x)
    return "\n".join(blocks)


def process_error_blocks(block_string):
    blocks = []
    for e in block_string.split("\nerror"):
        if e:
            if e.startswith("error"):
                blocks.append(e)
            else:
                blocks.append(f"error{e}")
    return blocks


def create_error_report(std_err):
    if not std_err:
        return []
    error_blocks = create_error_blocks(std_err)
    error_blocks = process_error_blocks(error_blocks)
    err_regex = r"error\[?([^\]]+)?\]?:\s*(.*)\s*\n\s*-->\s*(.*):(\d+):(\d+)([\s\S]*)"
    error_set = set()
    err_regex_other_error = r""
    errors = []
    for e in error_blocks:
        match = re.match(err_regex, e)
        if match:
            groups = match.groups()
            if len(groups) == 5:
                error_code = ""
                error_message = groups[0]
                file_path = groups[1]
                row, col = groups[2], groups[3]
                error_snippet = groups[4]
            elif len(groups) == 6:
                error_code = groups[0]
                error_message = groups[1]
                file_path = groups[2]
                row, col = groups[3], groups[4]
                error_snippet = groups[5]
            else:
                raise ValueError(f"Error in parsing error: {e}")
            error_hash = error_message + file_path + row + col
            if error_hash not in error_set:
                errors.append(
                    {
                        "error_code": error_code,
                        "error_message": error_message.strip(),
                        "file_path": file_path.strip(),
                        "row": row.strip(),
                        "col": col.strip(),
                        "error_snippet": error_snippet.strip(),
                    }
                )
                error_set.add(error_hash)
            # if error_code == "E0432":
            #     raise ValueError(f"Error in parsing error: {errors[-1]}")
    # sort errors by first file path and then line number
    errors = sorted(
        errors,
        key=lambda x: (
            x["error_code"] or "ZZZZ",
            x["file_path"] or "ZZZZ",
            int(x["row"]) or int(1e9),
            int(x["col"]) or int(1e9),
            x["error_message"] or "ZZZZ",
            x["error_snippet"] or "ZZZZ",
        ),
    )
    return errors


def analyse_errors(std_err):
    errors = create_error_report(std_err)
    if any(e not in ERROR_DICT for e in [e["error_code"] for e in errors]):
        error_dict = build_error_dict([e["error_code"] for e in errors])
    else:
        error_dict = ERROR_DICT
    return errors, error_dict


def build_error_dict(errors):
    t = {}
    for e in errors:
        if e == "" or e == None:
            t[e] = "other errors"
        else:
            res = subprocess.run(
                ["rustc", "--explain", e], capture_output=True, text=True
            )
            # process error till Erroneous code example:
            res_stdout = res.stdout.split("Erroneous code example:")[0].replace(
                "\n", " "
            )
            t[e] = res_stdout

    for e in ERROR_DICT:
        if e in t.keys():
            t[e] = ERROR_DICT[e]
    for e in t:
        if e not in ERROR_DICT:
            ERROR_DICT[e] = t[e]
    with open(ERROR_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(ERROR_DICT, f)
    return t
def cargo_test(proj_path):
    try:
        result = subprocess.run(
        ["cargo", "test" ], cwd=proj_path, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        return -1, -1
    std_out = result.stdout
    std_err = result.stderr
    oks = std_out.count('... ok')
    fails = std_out.count('... FAILED')
    return oks, fails

def performance_stats(dir):
    lines = csv.reader(open(dir / 'test_report.csv', 'r'))
    proj_dict = {}
    lines = list(lines)
    for line in tqdm(lines[1:]):
        proj_name = line[0]
        err_code = line[1]
        if proj_name in proj_dict:
            continue
        oks, fails = cargo_test(dir/proj_name)
        line.append(oks)
        line.append(fails)
            
        if err_code != "No errors":
            proj_dict[proj_name] = (-1, -1)
        else:
            proj_dict[proj_name] = (oks, fails)
    with open(Path(dir)/ 'test_report_p_f.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)
    with open(Path(dir)/ 'model_perf.csv', 'w') as f:
        writer = csv.writer(f)
        visited = set()
        writer.writerow(['Project', 'OKs', 'Fails'])
        for line in lines[1:]:
            if line[0] in visited:
                continue
            writer.writerow([line[0], proj_dict[line[0]][0], proj_dict[line[0]][1]])
            visited.add(line[0])
    return proj_dict
def aggregate_performance_stats(dir_paths: List[Path], output_folder: Path):
    proj_stats = {}
    for dir_path in dir_paths:
        with open(dir_path / 'model_perf.csv', 'r') as f:
            lines = csv.reader(f)
            lines = list(lines)
            for line in lines[1:]:
                if line[0] not in proj_stats:
                    proj_stats[line[0]] = []
                proj_stats[line[0]].append(line[1:])
    with open(output_folder / 'model_perf.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Project', 'OKs', 'Fails', 'Proj dir'])
        for proj in proj_stats:
            best_oks = -1
            best_idx = -1
            for idx,stat in enumerate(proj_stats[proj]):
                if best_oks == -1 or int(stat[0]) > best_oks:
                    best_oks = int(stat[0])
                    best_idx = idx
            writer.writerow([proj, proj_stats[proj][best_idx][0], proj_stats[proj][best_idx][1], dir_path])
    return proj_stats


def aggregate_results(dir_paths: List[Path], output_folder: Path):
    proj_paths = {}
    for dir_path in dir_paths:
        for proj_path in dir_path.iterdir():
            if proj_path.is_dir() and "Cargo.toml" in os.listdir(proj_path):
                if proj_path.name not in proj_paths:
                    proj_paths[proj_path.name] = []
                proj_paths[proj_path.name].append(proj_path)
    project_errors = {}
    for proj in proj_paths:
        # find the errors for each project
        proj_errors = []
        for proj_path in proj_paths[proj]:
            # compile the project
            errors = compile_rust_test_proj(proj_path) 
            err_rept = create_error_report(errors)
            proj_errors.append(err_rept)
        if proj not in project_errors:
            project_errors[proj] = []
        project_errors[proj].append(proj_errors)
    # write the errors to a file
    with open(output_folder / "error_report.json", "w") as f:
        json.dump(project_errors, f, indent=4)
    best_proj_errors = {}
    for p in project_errors:
        # we have selected a project
        min_errors = None
        for proj_err in project_errors[p]:
            if min_errors is None or len(proj_err) < len(min_errors):
                min_errors = proj_err
                best_proj_errors[p] = min_errors
    with open(dir_paths[0].parent / "best_error_report.json", "w") as f:
        json.dump(best_proj_errors, f, indent=4)
    
    # compute the test performance
    aggregate_performance_stats(dir_paths, output_folder)
    return best_proj_errors


if __name__ == "__main__":
    error_list = []
    dir_path = Path(sys.argv[1])
    for proj_path in dir_path.iterdir():
        if proj_path.is_dir():
            if "Cargo.toml" not in os.listdir(proj_path):
                continue
            errors, _ = compile_rust_proj(proj_path)
            print(f"Errors in {proj_path}")
            print(errors)
            if errors:
                with open(proj_path / "error_log.txt", "w") as f:
                    f.write(json.dumps(errors))
                error_list.append(errors)
    with open(dir_path / "error_list.txt", "w") as f:
        f.write(json.dumps(error_list))
    print("Compilation done")
