import os
import glob
import json
import argparse
import numpy as np
from tqdm import tqdm
from parser import remove_unused_functions, parse_python_code
from puzzle import execute_code, validate_and_convert_grid, Grid


def generate_output_grid(output_code: str, input_grid: Grid) -> Grid | None:
    result = {}
    result["input_grid"] = np.array(input_grid, dtype=np.int8)
    code = output_code + "\noutput_grid = generate_puzzle_output(input_grid)"
    try:
        execute_code(code, result, timeout=1)
    except TimeoutError:
        raise TimeoutError
    except:
        return None
    output_grid = validate_and_convert_grid(result.get("output_grid"))
    if not output_grid:
        return None
    if output_grid == input_grid:
        return None
    return output_grid


def generate_grids(solutions_mask: str, input_grids_prefix: str, output_grids_prefix: str, min_solutions_per_puzzle: int):

    puzzle_files = glob.glob(solutions_mask + "/completions/0.md")
    print(f"Found {len(puzzle_files)} solution puzzles in {solutions_mask}")

    num_skipped_puzzles = 0
    num_existing_grids = 0

    for file_name in tqdm(puzzle_files, desc="Generating output grids"):

        puzzle_dir = os.path.dirname(os.path.dirname(file_name))
        puzzle_parts = puzzle_dir.split("/")
        puzzle_name = puzzle_parts[-1]
        puzzle_batch = puzzle_parts[-2]
        puzzle_version = puzzle_parts[-3]

        grids_output_json = f"{output_grids_prefix}/{puzzle_version}/{puzzle_batch}/{puzzle_name}.json"
        if os.path.exists(grids_output_json):
            num_existing_grids += 1
            continue

        grids_input_json = f"{input_grids_prefix}/{puzzle_version}/{puzzle_batch}/{puzzle_name}.json"
        if not os.path.exists(grids_input_json):
            num_skipped_puzzles += 1
            continue

        try:
            with open(grids_input_json, "r") as f:
                input_grids = json.load(f)
            assert len(input_grids) == 30
        except:
            print(f"Error loading {grids_input_json}")
            num_skipped_puzzles += 1
            continue

        output_codes = []
        for i in range(20):
            if not os.path.exists(f"{puzzle_dir}/completions/{i}.md"):
                break
            with open(f"{puzzle_dir}/completions/{i}.md", "r") as f:
                output_code = f.read()
            output_code = parse_python_code(output_code)
            if output_code is None:
                break
            try:
                output_code = remove_unused_functions(output_code)
            except:
                break
            if "def generate_puzzle_output(" not in output_code:
                break
            output_codes.append(output_code)
        if len(output_codes) < min_solutions_per_puzzle:
            num_skipped_puzzles += 1
            continue

        data = []
        try:
            for i, (seed, input_grid) in enumerate(input_grids):
                for j, output_code in enumerate(output_codes):
                    output_grid = generate_output_grid(output_code, input_grid)
                    data.append({
                        "gid": i,
                        "sid": j,
                        "grid": output_grid,
                    })
        except TimeoutError:
            print(f"TimeoutError for {puzzle_name}")
            num_skipped_puzzles += 1
            continue

        os.makedirs(os.path.dirname(grids_output_json), exist_ok=True)
        with open(grids_output_json, "w") as f:
            json.dump({"grids": data, "codes": output_codes}, f)

    print(f"Skipped {num_skipped_puzzles} puzzles")
    print(f"Skipped {num_existing_grids} existing grids")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--solutions-mask", type=str, default="synthetic/solutions/nvarc_training/*/*")
    parser.add_argument("--input-grids-prefix", type=str, default="synthetic/grids30_input")
    parser.add_argument("--output-grids-prefix", type=str, default="synthetic/grids30_output")
    parser.add_argument("--min-solutions-per-puzzle", type=int, default=20)
    args = parser.parse_args()

    generate_grids(
        args.solutions_mask,
        args.input_grids_prefix,
        args.output_grids_prefix,
        args.min_solutions_per_puzzle,
    )