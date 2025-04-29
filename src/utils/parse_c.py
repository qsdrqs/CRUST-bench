import json
import os
from pathlib import Path
import re
import copy
import sys
from tree_sitter import Language, Parser
import subprocess

Language.build_library(
    "c_build/my-languages.so",
    ["./resources/tree-sitter-c"],
)
C_LANGUAGE = Language("c_build/my-languages.so", "c")
PARSER = Parser()
PARSER.set_language(C_LANGUAGE)


def find_dependencies(benchmark):
    file_dict = {}
    for file in benchmark.c_files:
        files_to_include = set()
        content = file["content"]
        includes = re.findall(r'#include "(.*)"', content)
        for include in includes:
            if file["file_name"].split(".")[0] == include.split("/")[-1].split(".")[0]:
                continue
            include = include.split("/")[-1]
            files_to_include.add(include)
        file_dict[file["file_name"]] = list(files_to_include)
    return file_dict


# given the dependencies, create an order of files to be transpiled
def order_dependencies(benchmark):
    file_dict = find_dependencies(benchmark)
    org_file_dict = copy.deepcopy(file_dict)
    ordered_files = []
    cntr = 0
    circ = False
    while file_dict:
        cntr += 1
        stop_flag = True
        for file in list(file_dict.keys()):
            if not file_dict[file]:
                ordered_files.append(file)
                del file_dict[file]
                for f in file_dict:
                    if file in file_dict[f]:
                        stop_flag = False
                        file_dict[f].remove(file)
            else:
                # check if all dependencies exist in file_dict
                for dep in file_dict[file]:
                    if dep in file_dict:
                        stop_flag = False
                if stop_flag:
                    ordered_files.append(file)
                    del file_dict[file]
                    break
        if stop_flag:
            break
        if cntr > 100:
            circ = True
            break
    if circ:
        ordered_files = []
        # order files based on the number of dependencies
        ordered_files = sorted( # type: ignore
            org_file_dict.keys(), key=lambda x: len(org_file_dict[x]),
        )
    return ordered_files, org_file_dict


def extract_function_declarations_and_globals(source_code):
    tree = PARSER.parse(source_code.encode("utf8"))
    root_node = tree.root_node

    functions = []
    globals = []
    structs = []

    def traverse(node):
        if node.type == "preproc_def" or node.type == "preproc_ifdef":
            globals.append(node.text.decode("utf8").strip())
        if node.type == "function_definition" or node.type == "declaration":
            type_specifier = None
            declarator_list = []
            # Look for the type specifier
            primitive_type = []
            function_declarator = []
            for child in node.children:
                # print(f'child: {child.type}, {child.text.decode("utf8")}')
                if (
                    child.type == "primitive_type"
                    or child.type == "type_identifier"
                    or child.type == "sized_type_specifier"
                ):
                    primitive_type.append(child.text.decode("utf8").strip())
                elif child.type == "function_declarator":
                    function_declarator.append(child.text.decode("utf8").strip())
                elif child.type == "pointer_declarator":
                    function_declarator.append(child.text.decode("utf8").strip())
            for p, f in zip(primitive_type, function_declarator):
                if f.startswith("*"):
                    functions.append(f"{p}{f}")
                else:
                    functions.append(f"{p} {f}")

            if type_specifier:
                for decl in declarator_list:
                    globals.append(f"{type_specifier} {decl}")

        elif node.type == "struct_specifier":
            struct_text = node.text.decode("utf8").strip()
            structs.append(struct_text)
        elif node.type == "type_definition":
            text = node.text.decode("utf8").strip()
            globals.append(text)

        if node.type == "function_definition" or node.type == "type_definition":
            pass
        else:
            for child in node.children:
                traverse(child)

    traverse(root_node)

    return functions, globals, structs


def get_c_functions(source_code):
    tree = PARSER.parse(bytes(source_code, "utf8"))
    root_node = tree.root_node
    functions = []
    try:
        traverse_with_function_args(root_node, functions)
    except Exception as e:
        print(f"Error in file: {source_code}")
        raise e
    return functions


def traverse_with_function_args(node, functions):
    if node.type == "declaration":
        return_type = ""
        function_name = ""
        arguments = []
        for child in node.children:
            if child.type == "primitive_type" or child.type == "type_identifier":
                # Capture the return type
                return_type += child.text.decode("utf8").strip() + " "
            elif (
                child.type == "function_declarator"
                or child.type == "pointer_declarator"
            ):
                # Extract function name and arguments
                for decl_child in child.children:
                    if decl_child.type == "identifier":
                        function_name = decl_child.text.decode("utf8").strip()
                    elif decl_child.type == "parameter_list":
                        # Extract arguments
                        for param in decl_child.children:
                            if param.type in {"parameter_declaration"}:
                                args = {}
                                for param_child in param.children:
                                    if (
                                        param_child.type == "type_identifier"
                                        or param_child.type == "primitive_type"
                                    ):
                                        args["type"] = param_child.text.decode(
                                            "utf8"
                                        ).strip()
                                    elif (
                                        param_child.type == "pointer_declarator"
                                        or param_child.type == "identifier"
                                    ):
                                        args["name"] = param_child.text.decode(
                                            "utf8"
                                        ).strip()
                                arguments.append(args)
                    elif (
                        decl_child.type == "function_declarator"
                        or decl_child.type == "pointer_declarator"
                    ):
                        for decl in decl_child.children:
                            if decl.type == "*":
                                function_name = "*" + function_name
                            elif decl.type == "identifier":
                                function_name += decl.text.decode("utf8").strip()
                            elif decl.type == "parameter_list":
                                # Extract arguments
                                for param in decl.children:
                                    args = {}
                                    if param.type in {"parameter_declaration"}:
                                        for param_child in param.children:
                                            if (
                                                param_child.type == "type_identifier"
                                                or param_child.type == "primitive_type"
                                            ):
                                                args["type"] = param_child.text.decode(
                                                    "utf8"
                                                ).strip()
                                            elif (
                                                param_child.type == "pointer_declarator"
                                                or param_child.type == "identifier"
                                            ):
                                                args["name"] = param_child.text.decode(
                                                    "utf8"
                                                ).strip()
                                        arguments.append(args)
                                        # arguments.append(param.text.decode("utf8").strip())
                            elif decl_child.type == ";":
                                pass
                    elif decl_child.type == "*":
                        function_name = "*" + function_name
                    elif decl_child.type == "ERROR":
                        pass
                    else:
                        traverse_with_function_args(node, functions)
                        raise Exception(f"Unknown type: {decl_child.type}")
            elif child.type == ";":
                pass
            elif child.type == "ERROR":
                pass
            else:
                raise Exception(f"Unknown type: {child.type}")
        if function_name.startswith("*"):
            function_name = function_name[1:]
            return_type = return_type + "*"
        functions.append(
            {
                "function_name": function_name,
                "return_type": return_type.strip(),
                "arguments": arguments,
            }
        )
    elif node.type == "struct_specifier":
        pass
    else:
        for child in node.children:
            traverse_with_function_args(child, functions)


def generate_header_file(functions, globals, structs):
    header_lines = []

    # Adding global variable declarations
    if globals or structs:
        header_lines.append("// Global Variables")
        for g in globals:
            header_lines.append(f"{g};")
        for s in structs:
            header_lines.append(f"{s};")
        header_lines.append("")
    if functions:
        header_lines.append("// Function Declarations")

        # Adding function declarations
        for f in functions:
            header_lines.append(f"{f};")

    return "\n".join(header_lines)


def get_header_files(benchmark):
    all_header_files = []
    c_file_dict = {f["file_name"]: f["content"] for f in benchmark.c_files}

    c_files = [
        f["file_name"].split(".")[0]
        for f in benchmark.c_files
        if f["file_name"].endswith(".c")
    ]
    h_files = [
        f["file_name"].split(".")[0]
        for f in benchmark.c_files
        if f["file_name"].endswith(".h")
    ]
    common_files = set(c_files) & set(h_files)
    for f in common_files:
        # do something
        c_file = c_file_dict[f + ".c"]
        h_file = c_file_dict[f + ".h"]
        c_func, c_glob, c_struct = extract_function_declarations_and_globals(c_file)
        h_func, h_glob, h_struct = extract_function_declarations_and_globals(h_file)
        all_func = set(c_func + h_func)
        all_glob = set(c_glob + h_glob)
        all_struct = set(c_struct + h_struct)
        header_file = generate_header_file(all_func, all_glob, all_struct)
        all_header_files.append({"file_name": f + ".h", "content": header_file})
    not_common = set(c_files).union(set(h_files)) - common_files
    for f in not_common:
        file_name = ""
        if f + ".h" in c_file_dict:
            file_name = f + ".h"
        else:
            file_name = f + ".c"

        func, glob, struct = extract_function_declarations_and_globals(
            c_file_dict[file_name]
        )
        header_file = generate_header_file(func, glob, struct)
        all_header_files.append({"file_name": file_name, "content": header_file})
    return all_header_files


def get_header_files_old(benchmark):
    all_header_files = []
    c_file_dict = {f["file_name"]: f["content"] for f in benchmark.c_files}
    c_files = [
        f["file_name"].split(".")[0]
        for f in benchmark.c_files
        if f["file_name"].endswith(".c")
    ]
    h_files = [
        f["file_name"].split(".")[0]
        for f in benchmark.c_files
        if f["file_name"].endswith(".h")
    ]
    generate_header_files = [f + ".c" for f in c_files]
    extra_header_files = set(h_files) - set(c_files)
    for h in extra_header_files:
        all_header_files.append(
            {"file_name": h + ".h", "content": c_file_dict[h + ".h"]}
        )
    for g in generate_header_files:
        source_code = c_file_dict[g]
        functions, globals, structs = extract_function_declarations_and_globals(
            source_code
        )
        header_file = generate_header_file(functions, globals, structs)
        all_header_files.append(
            {"file_name": g.split(".")[0] + ".h", "content": header_file}
        )
    return all_header_files


if __name__ == "__main__":
    c_code = """
int add(int a, int b)
"""
    functions = get_c_functions(c_code)

    print(functions)
