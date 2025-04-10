
from prompters.test_repair import BulletPointTestRepairPrompterWithSystemInstructions
from test_repairer import TestRepairer
from endpoint_config import endpoint_resolver
from pathlib import Path
from utils.compile_rust_utils import (
    final_error_report,
    get_errors_for_iteration,
    final_test_report,
    performance_stats
)
from utils.rust_project_builder import write_rust_files
from compile_projects import test
from benchmark import Benchmark
import argparse

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_path', type=str, required=True)
    args = argparser.parse_args()
    input_path = Path(args.input_path)
    output_dir = input_path
    print("Performance stats")
    performance_stats(output_dir) 

if __name__ == '__main__':
    main()