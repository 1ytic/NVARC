import os

import json
import numpy as np

import io
import signal
from contextlib import redirect_stdout, redirect_stderr


Grid = list[list[int]]


def timeout_handler(signum, frame):
    raise TimeoutError("execution timed out")


def execute_code(code: str, result: dict, timeout: int = 1):
    # TODO: use constrained execution like here https://github.com/baryhuang/mcp-server-aws-resources-python/blob/main/src/mcp_server_aws_resources/server.py
    with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        try:
            exec(code, result)
        finally:
            signal.alarm(0)


def filter_input_tests(functions: dict[str, str]) -> str:
    code = ""
    for k, v in functions.items():
        if k.startswith("test_") and k+"(grid)" in v:
            code += f"\n{k}(input_grid)"
        elif k.startswith("test_") and k+"(input_grid)" in v:
            code += f"\n{k}(input_grid)"
        elif k.startswith("test_") and k+"(grid: np.ndarray)" in v:
            code += f"\n{k}(input_grid)"
        elif k.startswith("test_") and k+"(input_grid: np.ndarray)" in v:
            code += f"\n{k}(input_grid)"
        elif k.startswith("test_") and k+"()" in v:
            code += f"\n{k}()"
    return code


def copy_training_examples(puzzle_name: str, examples_dir: str):
    training_file = f"external/ARC-AGI-2/data/training/{puzzle_name}.json"
    with open(training_file, "r", encoding="utf8") as f:
        training_data = json.load(f)
    os.makedirs(examples_dir, exist_ok=True)
    for split in ["train", "test"]:
        for i, pair in enumerate(training_data[split]):
            with open(f"{examples_dir}/{split}{i}.json", "w", encoding="utf8") as f:
                json.dump(pair, f)


def validate_and_convert_grid(grid: np.ndarray) -> Grid | None:
    if type(grid) != np.ndarray:
        return None
    if grid.ndim != 2:
        return None
    if grid.shape[0] < 1 or grid.shape[1] < 1:
        return None
    if grid.shape[0] > 30 or grid.shape[1] > 30:
        return None
    try:
        if not np.all(np.isin(np.unique(grid), range(10))):
            return None
    except:
        return None
    return grid.astype(np.int8).tolist()