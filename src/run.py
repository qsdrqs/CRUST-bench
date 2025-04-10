import json
import os
import sys
import csv
from pathlib import Path
import argparse
import cProfile
from benchmark import load_benchmarks
from prompter import (
    Prompter,
    RepairPrompter,
)
import subprocess
from prompters.test_repair import BulletPointTestRepairPrompterWithSystemInstructions
from transpiler import Transpiler, TranspilerN
from test_repairer import TestRepairer
from utils.rust_project_builder import write_rust_files, write_rust_interfaces, write_rust_multi_files, create_top_level_cargo_toml
from utils.compile_rust_utils import (
    final_error_report,
    get_errors_for_iteration,
    final_test_report,
    aggregate_results,
    compile_rust_test_proj,
    performance_stats
)
import shutil
from endpoint_config import endpoint_resolver
from compile_projects import compile, test
from repairer import Repairer
from utils.parse_c import order_dependencies


class Runner:
    def __init__(
        self,
        benchmark_dir,
        output_dir,
        prompt,
        prompt_format,
        prompt_strategy,
        repairer_prompt,
        repairer_format,
        repairer_strategy,
        iterations,
        endpoint,
        include_headers,
        config,
        n,
        single_benchmark,
        rust_dir,
    ):
        self.benchmark_dir = Path(benchmark_dir)
        self.output_dir = Path(output_dir)

        self.benchmarks = load_benchmarks(self.benchmark_dir, self.output_dir)
        self.prompt = prompt
        self.prompt_format = prompt_format
        self.prompt_strategy = prompt_strategy
        self.repairer_prompt = repairer_prompt
        self.repairer_format = repairer_format
        self.repairer_strategy = repairer_strategy
        self.iterations = int(iterations)
        self.endpoint = endpoint
        self.include_headers = include_headers
        self.config = config
        self.n = n
        if rust_dir:
            for benchmark in self.benchmarks:
                shutil.rmtree(benchmark.rust_path)
                if not Path(rust_dir + "/" + benchmark.project_name).exists():
                    # try capitalizing the first letter of the project name
                    shutil.copytree(
                        rust_dir + "/" + benchmark.project_name[0].upper() + benchmark.project_name[1:],
                        benchmark.rust_path,
                    )
                else:
                    shutil.copytree(
                        rust_dir + "/" + benchmark.project_name, benchmark.rust_path
                    )
            # we need to reload the benchmarks given that we have changed the rust path
            self.benchmarks = load_benchmarks(self.benchmark_dir, self.output_dir)
            assert all(
                len(benchmark.rust_headers) > 0 for benchmark in self.benchmarks
            ), "Rust path not copied correctly"
        if single_benchmark:
            # check if start with a number
            if single_benchmark[0].isdigit():
                single_benchmark = "proj_" + single_benchmark
            single_benchmark = single_benchmark.replace("-", "_")
            self.benchmarks = [
                b for b in self.benchmarks if b.project_name == single_benchmark
            ]
 

    def transpile(self):
        prompter = Prompter(
            self.prompt, self.prompt_format, self.prompt_strategy, self.include_headers
        )

        transpiler = Transpiler(
            self.benchmarks, prompter, endpoint=self.endpoint, config=self.config
        )
        results, benchmarks = transpiler.run()
        self.benchmarks = benchmarks
        transpiler.log_benchmarks(results)
        for benchmark in self.benchmarks:
            write_rust_files(benchmark)
        compile_results = compile(self.output_dir, 0)

    def repair(self):
        compile_results = []
        for i in range(self.iterations):
            repair_prompter = RepairPrompter(
                self.repairer_prompt, self.repairer_format, self.repairer_strategy
            )
            repairer = Repairer(
                self.benchmarks, repair_prompter, i, self.endpoint, config=self.config
            )
            results, benchmarks = repairer.run()
            self.benchmarks = benchmarks
            repairer.log_results(results)
            for benchmark in self.benchmarks:
                write_rust_files(benchmark)
            compile_results.append(compile(self.output_dir, i + 1))

    
        

    def multi_gen(self):
        prompter = Prompter(
            self.prompt, self.prompt_format, self.prompt_strategy, self.include_headers
        )

        transpiler = TranspilerN(
            self.benchmarks, prompter, endpoint=self.endpoint, config=self.config, n=self.n
        )
        results, benchmarks_list = transpiler.run()
        for idx, benchmarks in enumerate(benchmarks_list):
            for benchmark in benchmarks:
                write_rust_multi_files(benchmark, idx)
            # create top level directory for each iteration
            create_top_level_cargo_toml(benchmarks[0][0].rust_path.parent / f"{idx}")
        # clean up directories that are not used
        for dir in self.output_dir.iterdir():
            # check if dir name is a number
            if dir.is_dir() and not dir.name.isdigit():
                shutil.rmtree(dir)
        
        # get ready for repair
        self.benchmarks = []
        for i in range(self.n):
            self.benchmarks = load_benchmarks(self.benchmark_dir , self.output_dir / str(i))
            compile_results = compile(self.output_dir / str(i), 0)
            self.repair()
            self.get_loc()
            final_error_report(self.output_dir / str(i))
            final_test_report(self.output_dir / str(i))
            get_errors_for_iteration(self.output_dir / str(i))
            performance_stats(self.output_dir / str(i))
            self.benchmarks = []
        # aggregate the results based on the benchmark name
        aggregate_results([self.output_dir / str(i) for i in range(self.n)], self.output_dir)

    def get_loc(self):
        with open(self.output_dir / "loc.csv", "w", newline="", encoding="utf-8") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["project", "c_loc", "rust_loc", "builds"])
            for benchmark in self.benchmarks:
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

    def test_perf(self, mode="test_normal"):
        if mode == "test_normal":
            self.transpile()
        self.repair()
        self.get_loc()
        final_error_report(self.output_dir)
        final_test_report(self.output_dir)
        get_errors_for_iteration(self.output_dir)
        performance_stats(self.output_dir)

    

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--benchmark_dir", type=str, required=True)
    argparser.add_argument("--rust_dir", type=str, required=False, default=None)
    argparser.add_argument("--output_dir", type=str, required=True)
    argparser.add_argument("--prompt", type=str, required=True)
    argparser.add_argument("--mode", type=str, default="normal")
    argparser.add_argument("--endpoint", type=str, required=True)
    argparser.add_argument("--prompt_format", type=str, required=True)
    argparser.add_argument("--prompt_strategy", type=str, required=True)
    argparser.add_argument("--repairer_prompt", type=str, required=True)
    argparser.add_argument("--repairer_format", type=str, required=True)
    argparser.add_argument("--repairer_strategy", type=str, required=True)
    argparser.add_argument("--iterations", type=str, required=True)
    argparser.add_argument("--include_headers", type=bool, default=True)
    argparser.add_argument("--single_benchmark", type=str, default=None)
    argparser.add_argument("--config", type=str, required=False, default=None)
    argparser.add_argument("--n", type=int, default=1)
    args = argparser.parse_args()
    config = endpoint_resolver(args.config, args.endpoint)

    def main():
        runner = Runner(
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
            prompt=args.prompt,
            prompt_format=args.prompt_format,
            prompt_strategy=args.prompt_strategy,
            repairer_prompt=args.repairer_prompt,
            repairer_format=args.repairer_format,
            repairer_strategy=args.repairer_strategy,
            iterations=args.iterations,
            endpoint=args.endpoint,
            include_headers=args.include_headers,
            config=config,
            single_benchmark=args.single_benchmark,
            rust_dir=args.rust_dir,
            n=args.n,
        )
        config = {}
        if args.config:
            with open(args.config, "r") as f:
                config = json.load(f)
        if args.mode == "test_normal":
            runner.test_perf(args.mode)
        elif args.mode == "multi_gen":
            print(f"Top-{args.n} generation, with temperature {config['temperature']}")
            runner.multi_gen()
        else:
            raise ValueError("Invalid mode")

    # Profile the main function
    profiler = cProfile.Profile()
    profiler.run("main()")
    profiler.dump_stats(args.output_dir + "/profile.prof")
