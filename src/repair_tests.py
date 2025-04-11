
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
def repair_tests(benchmarks, iterations, repairer_prompt:Path, endpoint, config, output_dir):
    test_results = []
    test(output_dir,0)
    for i in range(iterations):
        
        test_repair_prompter = BulletPointTestRepairPrompterWithSystemInstructions(
            repairer_prompt)
        repairer = TestRepairer(
            benchmarks, test_repair_prompter, i, endpoint, config=config
        )
        results, benchmarks = repairer.run()
        
        for benchmark in benchmarks:
            write_rust_files(benchmark)
        test(output_dir, i + 1)
        benchmarks = benchmarks
    final_error_report(output_dir)
    final_test_report(output_dir)
    get_errors_for_iteration(output_dir)
    performance_stats(output_dir)

def load_benchmarks(r_path: Path):
    C_BENCH = Path('../datasets/CBench')
    benchmarks = []
    for project in r_path.iterdir():
        if project.is_dir() and Path(project/'Cargo.toml').exists():
            project_name = project.name
            if Path(C_BENCH / project_name).exists():
                benchmarks.append(Benchmark(C_BENCH/ project_name, project))
            else:
                c_proj = project_name
                if 'proj_' in project_name:
                    c_proj = project_name.split('_')[1]
                    assert(c_proj != '')
                if Path(C_BENCH / c_proj).exists():
                    
                    benchmarks.append(Benchmark(C_BENCH / c_proj, project))
                else:
                    c_proj = project_name.replace('_', '-')
                    benchmarks.append(Benchmark(C_BENCH / c_proj, project))
    return benchmarks

def main():
    argparser = argparse.ArgumentParser(help='The given script repairs the projects based on the test cases.')
    argparser.add_argument('--input_path', type=str, required=True, help='Path to the input Rust project directory.')
    argparser.add_argument('--output_path', type=str, required=True, help='Path to the output directory for projects that have been repaired with test case feedback.')
    argparser.add_argument('--endpoint', type=str, required=True, help='Endpoint for the repairer.')
    argparser.add_argument('--config', type=str, required=False, default=None, help='Path to the config file (incase endpoint is deployed using vllm) for the repairer.')
    argparser.add_argument('--iterations', type=int, required=True, help='Number of iterations for the repair process.')
    args = argparser.parse_args()
    r_path = Path(args.input_path)
    output_dir = Path(args.output_path)
    config = args.config
    iterations = args.iterations
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    endpoint = args.endpoint
    repairer_prompt = Path('./prompts/test_repair_prompts/repair.txt')
    import shutil
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    for proj in r_path.iterdir():
        shutil.copytree(proj, output_dir / proj.name)
    
    if config != None:
        config = Path(config)
    config = endpoint_resolver(config, endpoint)
    
    benchmarks = load_benchmarks(output_dir)
    if Path(output_dir / 'CBench').exists():
        shutil.rmtree(output_dir / 'CBench')
    repair_tests(benchmarks, iterations, repairer_prompt, endpoint, config, output_dir)
    
if __name__ == "__main__":
    main()