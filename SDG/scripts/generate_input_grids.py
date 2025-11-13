import os
import glob
import json
import argparse
import random
import multiprocessing
from tqdm import tqdm
from parser import parse_functions, parse_python_code
from puzzle import filter_input_tests, execute_code, validate_and_convert_grid, Grid
import timeout_decorator


def validate_grids(grids: list[Grid]) -> bool:
    if len(grids) < 5:
        return False
    unique_colors = set()
    first_seed, first_grid = grids[0]
    num_equal_grids = 0
    for seed, grid in grids:
        if grid == first_grid:
            num_equal_grids += 1
        if len(grid) < 1 or len(grid) > 30:
            return False
        for row in grid:
            if len(row) < 1 or len(row) > 30:
                return False
            unique_colors.update(row)
    if num_equal_grids == len(grids):
        # Prefer to use different grids
        return False
    if len(unique_colors) == 1:
        # Prefer to use different colors
        return False
    return True


@timeout_decorator.timeout(10, use_signals=False)
def generate_input_grids(input_code: str, num_grids: int, seed: int) -> list[tuple[int, Grid]]:

    input_functions = parse_functions(input_code)
    if "generate_puzzle_input" not in input_functions:
        return []

    test_input = filter_input_tests(input_functions)
    if not test_input:
        return []

    unique_grids = []

    for _ in range(num_grids * 2):
        result = {}
        code = input_code + f"\ninput_grid = generate_puzzle_input({seed})" + test_input
        seed += 1
        try:
            execute_code(code, result)
        except TimeoutError:
            break
        except:
            continue
        grid = validate_and_convert_grid(result.get("input_grid"))
        if grid:
            do_exists = False
            for prev_seed, prev_grid in unique_grids:
                if grid == prev_grid:
                    do_exists = True
                    break
            if not do_exists:
                unique_grids.append((seed, grid))
                if len(unique_grids) == num_grids:
                    break
    
    if validate_grids(unique_grids):
        return unique_grids
    else:
        return []


def generate_grids(inputs_mask: str, grids_prefix: str, num_grids: int, init_seed: int):

    puzzle_files = glob.glob(inputs_mask)
    print(f"Found {len(puzzle_files)} input files in {inputs_mask}")

    num_existing_grids = 0
    num_skipped_puzzles = 0
    num_created_grids = 0

    random.seed(init_seed)

    for file_name in tqdm(puzzle_files, desc="Generating input grids"):

        puzzle_parts = file_name.split("/")
        puzzle_name = puzzle_parts[-1][:-3]
        puzzle_batch = puzzle_parts[-3]
        split_name = puzzle_parts[-4]
        grids_json = f"{grids_prefix}/{split_name}/{puzzle_batch}/{puzzle_name}.json"

        if os.path.exists(grids_json):
            num_existing_grids += 1
            continue

        with open(file_name, "r") as file:
            input_completion = file.read()
        
        input_code = parse_python_code(input_completion)
        if input_code is None:
            num_skipped_puzzles += 1
            continue

        try:
            input_grids = generate_input_grids(input_code, num_grids, init_seed)
        except timeout_decorator.timeout_decorator.TimeoutError as e:
            print(f"Skipping {puzzle_name} puzzle due to timeout!")
            num_skipped_puzzles += 1
            continue

        if len(input_grids) != num_grids:
            num_skipped_puzzles += 1
            continue

        os.makedirs(os.path.dirname(grids_json), exist_ok=True)

        with open(grids_json, "w") as file:
            json.dump(input_grids, file)

        init_seed = input_grids[-1][0] + 1
        num_created_grids += 1

    print(f"Skipped {num_skipped_puzzles} bad puzzles")
    print(f"Skipped {num_existing_grids} existing grids")
    print(f"Created {num_created_grids} grids")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs-mask", type=str, default="synthetic/inputs/nvarc_training/v1/completions/*.md")
    parser.add_argument("--grids-prefix", type=str, default="synthetic/grids30_input")
    parser.add_argument("--num-grids", type=int, default=30)
    parser.add_argument("--init-seed", type=int, default=-1)
    args = parser.parse_args()

    if args.init_seed == -1:
        init_seed = random.randint(0, 10000)
    else:
        init_seed = args.init_seed

    multiprocessing.set_start_method("fork")

    generate_grids(
        args.inputs_mask,
        args.grids_prefix,
        args.num_grids,
        init_seed,
    )