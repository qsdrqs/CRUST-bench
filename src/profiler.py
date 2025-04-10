from pathlib import Path
import os
import json
import re
import pstats
import argparse


def load_profiler(path):
    p = pstats.Stats(path)
    # print according to tottime
    p.strip_dirs().sort_stats("tottime").print_stats(20)
    return p


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--path", help="Path to the profiler results")
    args = argparser.parse_args()
    profiler = load_profiler(args.path)
