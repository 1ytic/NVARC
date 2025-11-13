import os
import glob
import json
import random
import numpy as np
from tqdm import tqdm
from datasets import Dataset


Grid = list[list[int]]


def dihedral_transform(arr: np.ndarray, tid: int) -> np.ndarray:
    """8 dihedral symmetries by rotate, flip and mirror"""
    if tid == 0:
        return arr
    elif tid == 1:
        return np.rot90(arr, k=1)
    elif tid == 2:
        return np.rot90(arr, k=2)
    elif tid == 3:
        return np.rot90(arr, k=3)
    elif tid == 4:
        return np.fliplr(arr)       # horizontal flip
    elif tid == 5:
        return np.flipud(arr)       # vertical flip
    elif tid == 6:
        return arr.T                # transpose (reflection along main diagonal)
    elif tid == 7:
        return np.fliplr(np.rot90(arr, k=1))  # anti-diagonal reflection
    else:
        raise ValueError(f"Invalid transformation: {tid}")


def color_mapping(grid, mapping):
    for old_color, new_color in enumerate(mapping):
        grid[grid == old_color] = new_color
    return grid


def fix_settings(rules):
    if not rules:
        return []
    fixed_rules = []
    for augmentation in rules:
        if augmentation == "dihedral":
            tid = random.randint(0, 7)
            fixed_rules.append({"type": "dihedral", "settings": {"tid": tid}})
        elif augmentation == "color":
            colors = list(range(0, 10))
            random.shuffle(colors)
            fixed_rules.append({"type": "color", "settings": {"mapping": colors}})
        else:
            raise ValueError(f"Unsupported augmentation: {augmentation}")
    return fixed_rules


def apply_augmentation(pairs, rules):
    transformed_pairs = []
    for sample in pairs:
        input_grid = np.array(sample["input"], dtype=np.uint8)
        output_grid = np.array(sample["output"], dtype=np.uint8)
        for rule in rules:
            settings = rule["settings"]
            if rule["type"] == "dihedral":
                input_grid = dihedral_transform(input_grid, settings["tid"])
                output_grid = dihedral_transform(output_grid, settings["tid"])
            elif rule["type"] == "color":
                input_grid = color_mapping(input_grid, settings["mapping"])
                output_grid = color_mapping(output_grid, settings["mapping"])
        transformed_pairs.append({"input": input_grid.tolist(), "output": output_grid.tolist()})
    return transformed_pairs


def validate_grid(grid: Grid) -> bool:
    array = np.array(grid, dtype=np.int8)
    if array.ndim != 2:
        return False
    if array.shape[0] < 1 or array.shape[0] > 30:
        return False
    if array.shape[1] < 1 or array.shape[1] > 30:
        return False
    if not np.all(np.isin(array, np.arange(10))):
        return False
    return True


def validate_pairs(pairs: list[dict[str, Grid]]) -> bool:
    unique_input_shapes = set()
    unique_output_shapes = set()
    unique_input_grids = set()
    unique_output_grids = set()
    unique_input_colors = set()
    unique_output_colors = set()
    for pair in pairs:
        input_grid = pair["input"]
        output_grid = pair["output"]
        input_hash = hash(tuple(map(tuple, input_grid)))
        output_hash = hash(tuple(map(tuple, output_grid)))
        unique_input_grids.add(input_hash)
        unique_output_grids.add(output_hash)
        unique_input_shapes.add((len(input_grid), len(input_grid[0])))
        unique_output_shapes.add((len(output_grid), len(output_grid[0])))
        for row in input_grid:
            unique_input_colors.update(row)
        for row in output_grid:
            unique_output_colors.update(row)
    if len(unique_input_grids) != len(pairs):
        # Prefer to use different input grids
        return False
    if len(unique_output_grids) == 1:
        # Output grids are all the same
        return False
    if len(unique_input_colors) == 1 and len(unique_input_shapes) == 1:
        # Prefer to use grids with different colors or shapes
        return False
    if len(unique_output_colors) == 1 and len(unique_output_shapes) == 1:
        # Prefer to use grids with different colors or shapes
        return False
    return True


def convert_grid_to_string(grid: Grid) -> str:
    assert validate_grid(grid), grid
    text = ""
    for row in grid:
        for cell in row:
            text += str(int(cell))
        text += "\n"
    return text.strip()


def get_messages(pairs: list[dict[str, Grid]], do_augmentation=False):
    if do_augmentation:
        augmentation = fix_settings(["dihedral", "color"])
        pairs = apply_augmentation(pairs, augmentation)
    messages = []
    for sample in pairs:
        messages.append({"role": "user", "content": convert_grid_to_string(sample["input"])})
        messages.append({"role": "assistant", "content": convert_grid_to_string(sample["output"])})
    return messages


def convert_arc_to_messages(path_mask: str, num_samples: int = 256, seed: int = 42):
    random.seed(seed)
    rearc_puzzle_names = [file.replace(".json", "") for file in sorted(os.listdir("external/re-arc/re_arc/tasks"))]
    result = []
    num_skipped_puzzles = 0
    num_skipped_messages = 0
    for file in tqdm(sorted(glob.glob(path_mask))):
        puzzle_name = os.path.basename(file).replace(".json", "")
        if puzzle_name in rearc_puzzle_names:
            num_skipped_puzzles += 1
            continue
        with open(file) as f:
            data = json.load(f)
        pairs = data["train"] + data["test"]
        if not validate_pairs(pairs):
            print(f"Bad pairs for {puzzle_name}")
            num_skipped_messages += 1
            continue
        for i in range(num_samples):
            if i > 0:
                random.shuffle(pairs)
            puzzle_messages = get_messages(pairs, do_augmentation=i > 0)
            result.append({"puzzle_name": puzzle_name, "messages": puzzle_messages})
    if num_skipped_puzzles > 0:
        print(f"Skipped {num_skipped_puzzles} puzzles")
    if num_skipped_messages > 0:
        print(f"Skipped {num_skipped_messages} messages")
    ds = Dataset.from_list(result)
    return ds


def convert_rearc_to_messages(seed: int = 42, num_samples: int = 256):
    random.seed(seed)
    result = []
    num_skipped_messages = 0
    for file in tqdm(sorted(glob.glob("external/re-arc/re_arc/tasks/*.json"))):
        puzzle_name = os.path.basename(file).replace(".json", "")

        with open(file) as f:
            data = json.load(f)
        assert len(data) == 2048
        
        cleaned_data = []
        for pair in data:
            if validate_grid(pair["input"]) and validate_grid(pair["output"]):
                cleaned_data.append(pair)

        random.shuffle(cleaned_data)

        for _ in range(num_samples):
            num_pairs = random.randint(6, 7)
            pairs = [cleaned_data.pop() for _ in range(num_pairs)]
            if not validate_pairs(pairs):
                num_skipped_messages += 1
                continue
            messages = get_messages(pairs, do_augmentation=True)
            result.append({"puzzle_name": puzzle_name, "messages": messages})
    
    if num_skipped_messages > 0:
        print(f"Skipped {num_skipped_messages} messages")
    ds = Dataset.from_list(result)
    return ds


def convert_synthetic_to_messages(mask: str, seed: int = 42, num_samples: int = 16):
    random.seed(seed)

    pairs_files = sorted(glob.glob(mask))
    print(f"Found {len(pairs_files)} pairs files")

    result = []
    num_skipped_messages = 0
    for pairs_file in tqdm(pairs_files):

        puzzle_parts = pairs_file.split("/")
        puzzle_name = puzzle_parts[-1][:-5]

        with open(pairs_file, "r") as f:
            original_data = json.load(f)
        
        data = original_data.copy()
        random.shuffle(data)

        for _ in range(num_samples):
            num_pairs = random.randint(5, 6)
            if len(data) < num_pairs:
                data = original_data.copy()
                random.shuffle(data)
            pairs = [data.pop() for _ in range(num_pairs)]
            if not validate_pairs(pairs):
                num_skipped_messages += 1
                continue
            messages = get_messages(pairs, do_augmentation=True)
            result.append({"puzzle_name": puzzle_name, "messages": messages})

    if num_skipped_messages > 0:
        print(f"Skipped {num_skipped_messages} messages")
    return Dataset.from_list(result)


if __name__ == "__main__":

    output_path = "data/grids_v15"
    os.makedirs(output_path, exist_ok=True)

    ds = convert_arc_to_messages("external/ARC-AGI-2/data/evaluation/*.json", num_samples=6)
    ds.save_to_disk(f"{output_path}/arc2_evaluation6")
    print(ds)

    ds = convert_rearc_to_messages(seed=1)
    ds.save_to_disk(f"{output_path}/rearc")
    print(ds)

    ds = convert_arc_to_messages("external/ARC-AGI-2/data/training/*.json", seed=3)
    ds.save_to_disk(f"{output_path}/arc2_training")
    print(ds)

    ds = convert_arc_to_messages("external/MINI-ARC/data/MiniARC/*.json", seed=4)
    ds.save_to_disk(f"{output_path}/mini")
    print(ds)

    ds = convert_arc_to_messages("external/ConceptARC/corpus/*/*.json", seed=5)
    ds.save_to_disk(f"{output_path}/concept")
    print(ds)

    ds = convert_synthetic_to_messages("synthetic/pairs/nvarc_training/*/*.json", seed=6, num_samples=24)
    ds.save_to_disk(f"{output_path}/nvarc_training")
    print(ds)

    ds = convert_synthetic_to_messages("synthetic/pairs/nvarc_full/*/*.json", seed=7, num_samples=32)
    ds.save_to_disk(f"{output_path}/nvarc_full")
    print(ds)
