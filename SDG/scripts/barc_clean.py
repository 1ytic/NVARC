import os
import glob
import re
import pandas as pd
from utils import get_training_puzzle_names
from utils_barc import clean_concepts, clean_description, clean_code
from parser import parse_functions


training_puzzles = get_training_puzzle_names()


solutions = []
for file in glob.glob("external/BARC/seeds/*.py"):
    puzzle_name = os.path.basename(file)[:-3]
    if puzzle_name not in training_puzzles:
        print(f"Task {puzzle_name} is not in the training set.")
        continue
    with open(file, "r", encoding="utf8") as f:
        text = f.read()
    match = re.search(r"# concepts:(.+)\n# description:(.+)\ndef main", text, flags=re.DOTALL)
    if not match:
        print(f"Task {puzzle_name} does not have the required comments.")
        continue
    try:
        functions = parse_functions(text)
    except Exception as e:
        print(f"Error parsing functions in task {puzzle_name}: {e}")
        continue
    concepts = clean_concepts(match.group(1))
    description = clean_description(match.group(2))
    transformation_plan = clean_code(functions["main"])
    reconstruction_plan = clean_code(functions["generate_input"])
    solutions.append({
        "puzzle_name": puzzle_name,
        # "concepts": concepts,
        "description": description,
        # "transformation_plan": transformation_plan,
        # "reconstruction_plan": reconstruction_plan,
    })
print(f"Found {len(solutions)} solutions for training tasks.")

df = pd.DataFrame(solutions)

df = df.sort_values(["puzzle_name", "description"])

df.to_csv("data/barc_cleaned.csv", index=False)
