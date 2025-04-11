# CRUST-Bench: A Comprehensive Benchmark for C-to-safe-Rust Transpilation

Authors: Anirudh Khatry, Robert Zhang, Jia Pan, Ziteng Wang, Qiaochu Chen, Greg Durrett, Isil Dillig.

![Dataset Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Last Updated](https://img.shields.io/badge/last%20updated-April%202025-orange)

![CRUST-bench workflow](./src/resources/CRUST-bench.png)

## Overview

C-to-Rust transpilation is essential for modernizing legacy C code while enhancing safety and interoperability with modern Rust ecosystems. However, no dataset currently exists for evaluating whether a system can transpile C into safe Rust that passes a set of test cases. We introduce CRUST-Bench, a dataset of 100 C repositories, each paired with manually-written interfaces in safe Rust as well as test cases that can be used to validate correctness of the transpilation. By considering entire repositories rather than isolated functions, CRUST-Bench captures the challenges of translating complex projects with dependencies across multiple files. The provided Rust interfaces provide explicit specifications that ensure adherence to idiomatic, memory-safe Rust patterns, while the accompanying test cases enforce functional correctness. We evaluate state-of-the-art large language models (LLMs) on this task and find that safe and idiomatic Rust generation is still a challenging problem for various state-of-the-art methods and techniques. We also provide insights into the errors LLMs usually make in transpiling code from C to safe Rust. The best performing model, OpenAI o1, is able to solve only 15 tasks in a single-shot setting. Improvements on CRUST-Bench would lead to improved transpilation systems that can reason about complex scenarios and help in migrating legacy codebases from C into languages like Rust that ensure memory safety.

## Paper

Our paper "CRUST-Bench: A Comprehensive Benchmark for C-to-safe-Rust Transpilation" is available at:
- [arXiv](https://arxiv.org/abs/XXXX.XXXXX)

## Dataset Description

### Data Collection
We collected data from 100 Github repositories, spanning various domains like:
 - System utilities
 - Algorithms
 - Programming Language Infrastructure
 - Networking
 - Cryptography and Security
 - Data structures 
 - etc.


### Data Format
The dataset consists of 2 folders namely:
1. CBench
2. Rust Bench

```
CBench/
├── Project_1/
│   ├── file1.c/
│   ├── file2.c/
│   └── ...
├── Project_2/
│   ├── file1.c/
│   ├── file2.c/
│   └── ...
├── Project_3/
│   ├── file1.c/
│   ├── file2.c/
│   └── ...
└── ...

RBench/
├── Project_1/
│   ├── interfaces
│   │   ├── file1.rs
│   │   ├── file2.rs
│   │   └── ...
│   ├── bin
│   │   ├── test1.rs
│   │   ├── test2.rs
│   │   └── ...
├── Project_2/
│   ├── interfaces
│   │   ├── file1.rs
│   │   ├── file2.rs
│   │   └── ...
│   ├── bin
│   │   ├── test1.rs
│   │   ├── test2.rs
│   │   └── ...
│   └── ...
└── ...


```

## Usage

### Requirements
List any dependencies required to use the dataset:

```bash
pip install -r requirements.txt
```

### Loading the Dataset
The dataset is within the `datasets` folder as a zip file that can be extracted to provide 2 folders:
  1. __CBench__: the projects scraped from github.
  2. __RBench__: the manually annotated interfaces and corresponding tests.

To perform a sanity type check, we provide the `check_benchmarks/check_build.py` script that produces a compilable version of the rust project with the `unimplemented!()` function bodies that can be type checked.

The `src/dataset_stats` aids in plotting metrics over the C repositories and the annotated Rust interfaces and tests.

### Recreating experiments from CRUST-bench.
Please set the relevant OpenAI, Antropic, Google CLOUD API keys using the environment variables.

```bash
export OPENAI_API_KEY=<OpenAI_API_KEY>
export ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY>
export GOOGLE_CLOUD_PROJECT=<GOOGLE_CLOUD_PROJECT>
export GOOGLE_CLOUD_REGION=<GOOGLE_CLOUD_REGION>
```

Incase you want to test your own model, you need to define the respective model in the endpoints folder. We format all our requests in the `openai.chat.completions` API format. Ensure that you also update the `call_endpoint.py` file, and add the associated configuration of the model in the `configs` folder.

We provide easy bash scripts located in the `scripts` folder that allow you to easily test your models with our pipeline. 

The entrypoint to our code is the `src/run.py` file that takes in the following params:

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--benchmark_dir` | `str` | ✅ Yes | – | Path to the C project (**CBench**) directory. |
| `--rust_dir` | `str` | ❌ No | `None` | Path to the Rust project (**RBench**) directory. |
| `--output_dir` | `str` | ✅ Yes | – | Path to the output directory. |
| `--prompt` | `str` | ✅ Yes | – | Prompt to use for the model during transpilation. |
| `--mode` | `str` | ❌ No | `"normal"` | Transpilation mode. Options: `normal`, `multi_gen`. |
| `--endpoint` | `str` | ✅ Yes | – | Endpoint to use for the model. See `endpoints/call_endpoint.py` for details. |
| `--prompt_format` | `str` | ✅ Yes | – | Format of the prompt. Options: `markdown`, `bullet_point`. |
| `--prompt_strategy` | `str` | ❌ No | `"all"` | Strategy for composing the prompt. Options: `all` (all files are appended). |
| `--repairer_prompt` | `str` | ✅ Yes | – | Prompt used for the repairer model. |
| `--repairer_format` | `str` | ✅ Yes | – | Format of the repairer prompt. Options: `markdown`, `bullet_point`. |
| `--repairer_strategy` | `str` | ✅ Yes | – | Strategy for repairer prompt. Options: `all` (all files are appended). |
| `--iterations` | `str` | ✅ Yes | – | Number of iterations to run the repairer. |
| `--include_headers` | `bool` | ❌ No | `True` | Whether to include header files in the prompt. |
| `--single_benchmark` | `str` | ❌ No | `None` | Run a single benchmark only (provide its name). |
| `--config` | `str` | ❌ No | `None` | Path to the endpoint configuration file. |
| `--n` | `int` | ❌ No | `1` | Number of generations to request from the model during transpilation. |

The test based repair is only run for projects that build and test but do not pass all test cases. The associated bash script is provided in `scripts/test_based_repair/test_repair.sh`
## Citation

If you use this dataset in your research, please cite our paper:

```bibtex
@article{CRUST-bench,
  title=CRUST-Bench: A Comprehensive Benchmark for C-to-safe-Rust Transpilation,
  author={Last, First and Co-author, Second and et al.},
  journal={Journal/Conference Name},
  year={2025},
  volume={XX},
  pages={XXX-XXX},
  doi={10.XXXX/XXXXXXX}
}
```

## License

This dataset is released under [LICENSE NAME] license. See [LICENSE](LICENSE) for details.

## Contact

For questions, issues, or further information, please contact:
- **Name**: Anirudh Khatry
- **Email**: [akhatry@utexas.edu]
- **GitHub**: [@anirudhkhatry](https://github.com/anirudhkhatry)

## Acknowledgments

Acknowledge any funding sources, organizations, or individuals who contributed to the creation of this dataset.