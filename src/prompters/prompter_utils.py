import re


def prompt_format_parser(response):
    results = []
    # remove trailing whitespaces from the response
    response = "\n".join([r.strip() for r in response.split("\n")])
    raw_result_file_names_regex = re.compile(r"\{\{(.+?)\}\}\n*```")
    raw_result_file_names = raw_result_file_names_regex.findall(response)
    processed_raw_file_names = []
    for f in raw_result_file_names:
        if f.endswith(".rs"):
            processed_raw_file_names.append(f)
        else:
            processed_raw_file_names.append(f + ".rs")
    raw_result_code_regex = re.compile(r"\{\{.+?\}\}[\n]*```rust\n*([\s\S]+?)```")
    raw_result_code = raw_result_code_regex.findall(response)
    if len(processed_raw_file_names) != len(raw_result_code):
        if len(raw_result_code) > len(processed_raw_file_names):
            raw_result_code = raw_result_code[-len(processed_raw_file_names) :]
        return []
    for i in range(len(processed_raw_file_names)):
        results.append(
            {
                "file_name": processed_raw_file_names[i],
                "content": raw_result_code[i],
            }
        )
    return results


def markdown_parser(response):
    results = []
    raw_result_file_names_regex = re.compile(r"[\#]+\s*[`]?(.+\.rs)[`]?\n+```rust")
    raw_result_file_names = raw_result_file_names_regex.findall(response)
    rust_file_name_regex = re.compile(r"([^\s]+\.rs)")
    processed_raw_file_names = []
    for f in raw_result_file_names:
        file_name = rust_file_name_regex.findall(f)
        processed_raw_file_names.append(file_name[0])
    raw_result_code_regex = re.compile(r"[\#]+\s*.+\.rs\n+```rust\n*([\s\S]+?)```")
    raw_result_code = raw_result_code_regex.findall(response)
    if len(processed_raw_file_names) != len(raw_result_code):
        if len(raw_result_code) > len(processed_raw_file_names):
            raw_result_code = raw_result_code[-len(processed_raw_file_names) :]
        return []
    for i in range(len(processed_raw_file_names)):
        results.append(
            {
                "file_name": processed_raw_file_names[i],
                "content": raw_result_code[i],
            }
        )
    return results


def find_best_parser(response):
    res1 = prompt_format_parser(response)
    res2 = markdown_parser(response)
    if len(res1) > len(res2):
        return res1
    else:
        return res2
