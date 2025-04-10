from pathlib import Path
import os
import sys
import argparse
import csv
from utils.compile_rust_utils import (
    final_error_report,
    get_errors_for_iteration,
    final_test_report,
)
from benchmark import load_benchmarks
from compile_projects import compile
def get_loc(benchmarks, output_dir):
    with open(output_dir / "loc.csv", "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["project", "c_loc", "rust_loc", "builds"])
        for benchmark in benchmarks:
            res = benchmark.compile_rust()
            c_loc, rust_loc = benchmark.count_loc()
            if res == []:
                if rust_loc == 3:
                    builds = "Empty Project"
                else:
                    builds = "True"
            else:
                builds = "False"

            csv_writer.writerow([benchmark.project_name, c_loc, rust_loc, builds])
if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--rust_out", type=str, required=True)
    argparser.add_argument("--c_out", type=str, required=True)
    parsed = argparser.parse_args()

    rust_out = parsed.rust_out
    rust_out = Path(rust_out)
    c_out = parsed.c_out
    c_out = Path(c_out)
    benchmarks = load_benchmarks(c_out, rust_out)
    get_loc(benchmarks, rust_out)
    final_error_report(rust_out)
    final_test_report(rust_out)
    get_errors_for_iteration(rust_out)
