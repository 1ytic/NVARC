import os
import glob
import json
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm

Grid = list[list[int]]


def validate_grids(grids: list[Grid]) -> bool:
    unique_colors = set()
    first_grid = grids[0]
    num_equal_grids = 0
    for grid in grids:
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


def convert_grid_to_string(grid: np.ndarray) -> str:
    text = ""
    for row in grid:
        for cell in row:
            text += str(int(cell))
        text += "\n"
    return text.strip()


def grid_to_string(grid: Grid | None) -> str:
    if grid is None:
        return "none"
    return "|".join("".join(str(cell) for cell in row) for row in grid)


def string_to_grid(s: str) -> Grid:
    return [list(int(c) for c in row) for row in s.split("|")]


def filter_solutions(input_grids_prefix: str, output_grids_mask: str, output_prefix: str, min_majority_per_grid: int, min_pairs_per_puzzle: int, min_correct_solutions: int):
        
    output_grids_files = sorted(glob.glob(output_grids_mask))
    print(f"Found {len(output_grids_files)} output grids files")

    num_good_puzzles = 0

    for output_grids_file in tqdm(output_grids_files):

        puzzle_parts = output_grids_file.split("/")
        puzzle_name = puzzle_parts[-1][:-5]
        puzzle_batch = puzzle_parts[-2]
        puzzle_version = puzzle_parts[-3]

        with open(f"{input_grids_prefix}/{puzzle_version}/{puzzle_batch}/{puzzle_name}.json", "r") as f:
            input_grids = json.load(f)

        with open(output_grids_file, "r") as f:
            solutions = json.load(f)

        data = []
        for row in solutions["grids"]:
            data.append({
                "gid": row["gid"],
                "sid": row["sid"],
                "grid": grid_to_string(row["grid"]),
            })
        df = pd.DataFrame(data)

        data = []
        correct_sids = set()
        for gid, rows in df.groupby("gid"):
            stats = rows.grid.value_counts()
            best_grid = stats.idxmax()
            majority = stats[best_grid]
            if best_grid == "none":
                continue
            if majority < min_majority_per_grid:
                continue
            best_sids = rows.loc[rows.grid == best_grid].sid.tolist()
            wrong_sids = rows.loc[rows.grid != best_grid].sid.tolist()
            data.append({
                "gid": gid,
                "majority": majority,
                "solution": best_grid,
                "best_sids": ",".join([str(s) for s in best_sids]),
                "wrong_sids": ",".join([str(s) for s in wrong_sids]),
            })
            if len(correct_sids) == 0:
                correct_sids.update(best_sids)
            else:
                correct_sids.intersection_update(best_sids)
                if len(correct_sids) == 0:
                    break
        
        # Rule #1: At least min_pairs_per_puzzle pairs with majority >= min_majority_per_grid
        if len(data) < min_pairs_per_puzzle:
            continue

        # Rule #2: At least min_correct_solutions correct different solutions for all input grids
        if len(correct_sids) < min_correct_solutions:
            continue

        used_input_grids = []
        used_output_grids = []
        
        examples = []
        for example in data:
            gid = example["gid"]
            input_grid = input_grids[gid][1]
            output_grid = string_to_grid(example["solution"])
            used_input_grids.append(input_grid)
            used_output_grids.append(output_grid)
            examples.append({"input": input_grid, "output": output_grid})

        if validate_grids(used_input_grids) and validate_grids(used_output_grids):

            output_file = f"{output_prefix}/{puzzle_version}/{puzzle_batch}/{puzzle_name}.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(examples, f)

            num_good_puzzles += 1

    print(f"Found {num_good_puzzles} good puzzles")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-grids-prefix", type=str, default="synthetic/grids30_input")
    parser.add_argument("--output-grids-mask", type=str, default="synthetic/grids30_output/isorokin_v1/*/*.json")
    parser.add_argument("--output-prefix", type=str, default="synthetic/pairs")
    parser.add_argument("--min-majority-per-grid", type=int, default=8)
    parser.add_argument("--min-pairs-per-puzzle", type=int, default=12)
    parser.add_argument("--min-correct-solutions", type=int, default=4)
    args = parser.parse_args()

    filter_solutions(
        args.input_grids_prefix,
        args.output_grids_mask,
        args.output_prefix,
        args.min_majority_per_grid,
        args.min_pairs_per_puzzle,
        args.min_correct_solutions,
    )