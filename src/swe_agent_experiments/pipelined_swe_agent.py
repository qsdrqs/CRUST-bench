'''
Here the agent gets only the rust code and runs by repairing the code.
'''


from pathlib import Path
import json
import os
import sys
import subprocess
import argparse
sys.path.append('../')
import shutil
from compile_projects import compile
from utils.compile_rust_utils import (
    final_error_report,
    get_errors_for_iteration,
    final_test_report,
    performance_stats
)

SWE_AGENT_PATH = Path('../swe_agent')

DOCKER_IMAGE_PATH = 'anirudhkhatry/rust-python-env:latest'
PROBLEM_STATEMENT_PATH = Path('./problem_statements/ps2.md')
CARGO_PATH = Path('../resources/cache/dependencies.json')
CONFIG_PATH = Path('./config/rust_repair.yaml')


def run_command(command, cwd):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    return result

def run_swe_agent(benchmark_path, cost_limit, model):
    command = f'''
    python {str(SWE_AGENT_PATH)}/run.py \
        run \
        --agent.model.name={model} \
        --env.repo.path={benchmark_path} \
        --problem_statement.path={PROBLEM_STATEMENT_PATH} \
        --env.deployment.image={DOCKER_IMAGE_PATH} \
        --config={CONFIG_PATH} \
        --agent.model.per_instance_cost_limit={cost_limit} \
        --actions.apply_patch_locally=True
    '''
    result = run_command(command, cwd='./')
    with open(benchmark_path / 'sweagent.log', 'w') as f:
        f.write(result.stdout)
    with open(benchmark_path / 'sweagent.err', 'w') as f: 
        f.write(result.stderr)

def modify_cargo(benchmark_path):
    # cargo toml 
    cargo_toml = benchmark_path / 'Cargo.toml'
    lines=[]
    with open(cargo_toml, 'r', encoding="utf-8") as f:
        for line in f:
            if 'dependencies' in line:
                lines.append(line)
                break
            lines.append(line)
    with open(cargo_toml, 'w', encoding="utf-8") as f:
        for line in lines:
            f.write(line+'\n')
        json_data = json.loads(CARGO_PATH.read_text())
        for key, value in json_data.items():
            f.write(f'{key} = "{value}"\n')
        f.write('\n')

def git_init(benchmark_path):
    run_command(f'rm -rf .git', cwd=benchmark_path)
    run_command(f'git init', cwd=benchmark_path)
    run_command(f'git config --global --add safe.directory {benchmark_path}', cwd='./')
    run_command(f'git add .', cwd=benchmark_path)
    run_command(f'git commit -m "Initial commit"', cwd=benchmark_path)

def modify_folder(benchmark_path):
    # modify the folder structure
    for folder in benchmark_path.iterdir():
        src_path = benchmark_path / "src"
        if folder.is_dir() and folder.name != "src":
            shutil.rmtree(folder)
        interfaces_path = src_path / "interfaces"
        if interfaces_path.exists():
            shutil.rmtree(interfaces_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SWE Agent with specified parameters.")
    parser.add_argument("--input_path", type=str, required=True, help="Path to the input directory.")
    parser.add_argument("--output_path", type=str, required=True, help="Path to the output directory.")
    parser.add_argument("--cost_limit", type=float, required=True, help="Cost limit for the agent.")
    parser.add_argument("--model", type=str, required=True, help="Model to use for the agent.")
    args = parser.parse_args()
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    model = args.model
    if not input_path.exists():
        print(f"Input path {input_path} does not exist.")
        sys.exit(1)
    if not output_path.exists():
        output_path.mkdir(parents=True)
    cost_limit = args.cost_limit
    # copy all files from the input to the output directory
    for proj in input_path.iterdir():
        if proj.is_dir() and "Cargo.toml" in os.listdir(proj):
            if proj.name in os.listdir(output_path):
                print(f"Project {proj.name} already exists in output directory.")
                continue
            print(f"Processing project: {proj.name}")
            shutil.copytree(proj, output_path / proj.name, ignore=shutil.ignore_patterns('.git'))
            # modify the folder structure
            modify_folder(output_path / proj.name)
            # modify the Cargo.toml file
            modify_cargo(output_path / proj.name)                
            # git init
            print(f"Running git init for project: {proj.name}")
            git_init(output_path / proj.name)
            # run the swe agent
            print(f"Running SWE agent for project: {proj.name}")
            run_swe_agent(output_path / proj.name, cost_limit)
            run_command(f'git add .', cwd=output_path / proj.name)
            run_command(f'git commit -m "SWE Agent"', cwd=output_path / proj.name)
            # exit(0)
    # compute the result
    print(f"Compiling the output directory: {output_path}")
    compile(output_path, 0) # 0 is the iteration number
    final_error_report(output_path)
    final_test_report(output_path)
    get_errors_for_iteration(output_path)
    performance_stats(output_path)
