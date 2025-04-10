import os
import subprocess
import json
from pathlib import Path
import re


def find_cmake_or_makefile(directory):
    # Check for CMakeLists.txt file
    cmake_file = os.path.join(directory, "CMakeLists.txt")
    if os.path.isfile(cmake_file):
        return "cmake"

    # Check for common makefile names
    makefile_names = [
        "Makefile",
        "makefile",
        "GNUmakefile",
        "makefile.am",
        "makefile.in",
    ]
    for name in makefile_names:
        if os.path.isfile(os.path.join(directory, name)):
            return "make"

    return None


def build_c_project(directory):
    build_tool = find_cmake_or_makefile(directory)
    try:
        if build_tool == "cmake":
            print("CMake file found. Building the project with CMake...")
            try:
                subprocess.run(
                    ["mkdir", "-p", directory + "/build"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                subprocess.run(["cmake", ".."], check=True, cwd=directory + "/build")
                subprocess.run(
                    ["cmake", "--build", "."], check=True, cwd=directory + "/build"
                )
                return "success"
            except subprocess.CalledProcessError as e:
                return "error"
        elif build_tool == "make":
            print("Makefile found. Building the project with Make...")
            try:
                subprocess.run(["make"], check=True, cwd=directory, timeout=10)
                return "success"
            except subprocess.CalledProcessError as e:
                return "error"
        else:
            return "No make"
    except Exception as e:
        return "error"
