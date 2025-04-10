import subprocess
import os
from pathlib import Path
import csv
import argparse
def compile_rust_test_proj(proj_name):
    result = subprocess.run(
        ["cargo", "test"], cwd=proj_name, capture_output=True, text=True
    )
    std_out = result.stdout
    std_err = result.stderr
    oks = std_out.count('... ok')
    fails = std_out.count('... FAILED')
    
    return oks, fails

def compute_over_config(dir):
    lines = csv.reader(open(Path(dir)/ 'test_report.csv', 'r'))
    proj_dict = {}
    lines = list(lines)
    for line in lines[1:]:
        proj_name = line[0]
        err_code = line[1]
        oks, fails = compile_rust_test_proj(dir/proj_name)
        line.append(oks)
        line.append(fails)
        if err_code != "No errors":
            proj_dict[proj_name] = ("Error", "Error")
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
    
def over_endpoint(endpoint_path):
    endpoint_path = Path(endpoint_path)
    for dir in endpoint_path.iterdir():
        if dir.is_dir():
            for config in dir.iterdir():
                if config.is_dir():
                    if (config/'test_report.csv').exists():
                        compute_over_config(config)
                        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    compute_over_config(Path(parser.parse_args().config))