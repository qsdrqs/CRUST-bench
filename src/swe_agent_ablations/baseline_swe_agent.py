'''
this agent is given the c and rust folders and then runs by changing the interfaces of the rust code.
'''

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
from swe_ver1_compile import (
    compile,
    final_error_report,
    get_errors_for_iteration,
    final_test_report,
    performance_stats
)

DOCKER_IMAGE_PATH = 'anirudhkhatry/rust-python-env:latest'
PROBLEM_STATEMENT_PATH = Path('/mnt/nas/anirudh/C_to_Rust/scripts/swe_agent_ablations/ps1.md')
CARGO_PATH = Path('/mnt/nas/anirudh/C_to_Rust/scripts/resources/cache/dependencies.json')
CONFIG_PATH = Path('/mnt/nas/anirudh/SWE-agent/config/rust_transpiler.yaml')
SWE_AGENT_PATH = Path('/mnt/nas/anirudh/SWE-agent/sweagent/run')

def run_command(command, cwd):
    result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    return result

def run_swe_agent(benchmark_path, cost_limit):
    command = f'''
    python run.py \
        run \
        --agent.model.name=claude-3-5-sonnet-20241022 \
        --env.repo.path={benchmark_path} \
        --problem_statement.path={PROBLEM_STATEMENT_PATH} \
        --env.deployment.image={DOCKER_IMAGE_PATH} \
        --config={CONFIG_PATH} \
        --agent.model.per_instance_cost_limit={cost_limit} \
        --actions.apply_patch_locally=True
    '''
    result = run_command(command, cwd=SWE_AGENT_PATH)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SWE Agent with specified parameters.")
    parser.add_argument("--input_path", type=str, required=True, help="Path to the input directory.")
    parser.add_argument("--output_path", type=str, required=True, help="Path to the output directory.")
    parser.add_argument("--cost_limit", type=float, required=True, help="Cost limit for the agent.")
    args = parser.parse_args()
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    cost_limit = args.cost_limit
    print(f"Input path: {input_path}")
    # copy all files from the input to the output directory
    if not output_path.exists():
        output_path.mkdir(parents=True)
    for proj in input_path.iterdir():
        if proj.is_dir():
            # copy everthing excpet the .git folder
            shutil.copytree(proj, output_path / proj.name, ignore=shutil.ignore_patterns('.git'))            
            print(f'Processing {proj.name}')

            # modify the folder structure
            # modify the Cargo.toml file
            # modify_cargo(output_path / proj.name)                
            # git init
            print(f'git init {output_path / proj.name}')
            git_init(output_path / proj.name)
            # run the swe agent
            print(f'Running SWE agent on {output_path / proj.name}')
            run_swe_agent(output_path / proj.name, cost_limit)
            run_command(f'git add .', cwd=output_path / proj.name)
            run_command(f'git commit -m "SWE Agent"', cwd=output_path / proj.name) 
    # compute the result
    compile(output_path, 0) # 0 is the iteration number
    final_error_report(output_path)
    final_test_report(output_path)
    performance_stats(output_path)
