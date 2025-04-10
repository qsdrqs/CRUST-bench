import csv
from pathlib import Path
import argparse
import shutil
import json
CARGO_PATH = Path('./resources/cache/dependencies.json')
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

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--res_dir', type=str, required=True)
    arg_parser.add_argument('--output', type=str, required=True)
    args = arg_parser.parse_args()
    res_dir = Path(args.res_dir)
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    perf_path = res_dir / 'model_perf.csv'
    with open(perf_path, 'r') as f:
        # read lines
        data = csv.DictReader(f)
        data = list(data)
    projects_that_build_but_fail = []
    for row in data:
        if row['Fails'] != '-1' and row['Fails'] != '0':
            projects_that_build_but_fail.append(row['Project'])
    
    for proj in projects_that_build_but_fail:
        proj = Path(res_dir) / proj
        if proj.name == 'fs_c':
            # copy everything except the tmp directory -- this causes issues because of the way we copy
            if Path(proj / 'tmp').exists():
                shutil.rmtree(proj / 'tmp')
        shutil.copytree(proj, output / proj.name)
        modify_cargo(output / proj.name)
    print(f'Copied {len(projects_that_build_but_fail)} projects to {output}')