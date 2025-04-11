import argparse
from pathlib import Path
import sys
import os
import csv
import json
import subprocess
ERROR_DICT_PATH = Path('./resources/error_dict/error_dict.json')
with open(ERROR_DICT_PATH, 'r') as f:
    ERROR_DICT = json.load(f)
def find_unsafe_code(proj_path):
    unsafe_code = []
    for root, dirs, files in os.walk(proj_path):
        for file in files:
            if file.endswith('.rs'):
                with open(os.path.join(root, file), 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if 'unsafe' in line:
                            return True
    return False

def find_unsafe_code_dir(dir):
    unsafe = []
    for i in dir.iterdir():
        if i.is_dir():
            if find_unsafe_code_dir(i):
                unsafe.append(i)
    return unsafe
def process_proj(res_dir):
    build_error_csv = Path(res_dir) / 'test_report.csv'
    error_dict = {}
    unsafe = find_unsafe_code_dir(Path(res_dir))
    assert build_error_csv.exists(), f"File {build_error_csv} does not exist"
    with open(build_error_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            proj_name = row[0]
            error_code = row[1]
            error_msg = row[2]
            if error_code == '':
                error_code = error_msg
            if error_code not in error_dict:
                error_dict[error_code] = []
            if proj_name not in error_dict[error_code]:
                error_dict[error_code].append(proj_name)
    for error_code in error_dict:
        error_dict[error_code] = list(set(error_dict[error_code]))
    error_count = {}
    for error_code in error_dict:
        error_count[error_code] = len(error_dict[error_code])
    
    error_msg_cnt = {}
    for error_code in error_dict:
        if error_code in ERROR_DICT:
            error_msg_cnt[ERROR_DICT[error_code]] = error_dict[error_code]
        else:
            error_msg_cnt[error_code] = error_dict[error_code]
    
    new_error_msg_cnt = {}
    # process into groups
    for error_msg in error_msg_cnt:
        found = False
        for cat in [
            {'borrow': ['borrowed', 'borrow', 'moved', 'lifetime', 'lifetimes', "reference to a local variable"]},
            {'mutable_immutable': ['mutable', 'immutable']},
            {'unresolved import': ['import unresolved', "unresolved import", "unresolved imports"]},
            {'missing': ['missing', 'not found', 'cannot find', 'undeclared', 'Unresolved', 'non-existent', 'import']},
            {'trait': ['trait']},
            {'type': ['cast', 'sized types', 'bindings', 'type', 'identifier', 'expression', "dereference"]},
            {'args': ['args', 'argument', 'arguments', 'Something other than numbers and characters has been used for a range.']},
            ]:
            category, keywords = list(cat.items())[0]
            if any(keyword in error_msg.lower() for keyword in keywords):
                if category not in new_error_msg_cnt:
                    new_error_msg_cnt[category] = []
                new_error_msg_cnt[category].extend(error_msg_cnt[error_msg])
                found = True
                break
        if not found:
            new_error_msg_cnt[error_msg] = error_msg_cnt[error_msg]
            
    error_msg_cnt = new_error_msg_cnt
    
    for error_msg in error_msg_cnt:
        error_msg_cnt[error_msg] = list(set(error_msg_cnt[error_msg]))
        error_msg_cnt[error_msg] = len(error_msg_cnt[error_msg])
    error_msg_cnt['unsafe'] = len(unsafe)
    
    for error_msg in error_msg_cnt:
        error_msg_cnt[error_msg] = error_msg_cnt[error_msg] 
    with open(Path(res_dir) / 'error_distribution.json', 'w') as f:
        json.dump(error_msg_cnt, f, indent=4)

def get_numbers(path):
    model_perf_path = Path(path) / 'model_perf.csv'
    with open(model_perf_path, 'r') as f:
        reader= csv.DictReader(f)
        data = [row for row in reader]
    build_sucess = 0
    test_sucess = 0
    for row in data:
        if row['Fails'] != '-1':
            build_sucess += 1
        if row['Fails'] == '0':
            test_sucess += 1
    with open(path/'overall_stats', 'w') as f:
        f.write(f"Build success rate: {build_sucess/len(data)}\n")
        f.write(f"Test success rate: {test_sucess/len(data)}\n")
        f.write(f"Total projects: {len(data)}\n")
        f.write(f"Total build success: {build_sucess}\n")
        f.write(f"Total test success: {test_sucess}\n")
        f.write(f"Total build failure: {len(data) - build_sucess}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get error statistics')
    parser.add_argument('--input_path', type=str, help='results directory')
    args = parser.parse_args()
    process_proj(args.input_path)
    get_numbers(Path(args.input_path))
    

