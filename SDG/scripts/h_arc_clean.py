import pandas as pd
from utils import get_training_puzzle_names


def clean_solution(solution: str) -> str:
    lines = solution.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not line.endswith("."):
            line += "."
        cleaned_lines.append(line)
    return " ".join(cleaned_lines)


training_puzzles = get_training_puzzle_names()

df = pd.read_csv("external/h-arc/data/summary_data.csv")

df["puzzle_name"] = df.puzzle_name.apply(lambda x: x.replace(".json", ""))
df = df[df.puzzle_name.isin(training_puzzles)]
df = df[df.solved]
df = df[df.complete]
df = df[~df.last_written_solution.isnull()]

df["last_written_solution"] = df.last_written_solution.apply(clean_solution)
df = df[df.last_written_solution.str.len() > 50]

df = df.sort_values(["hashed_id", "puzzle_name", "attempt_number"])

df = df.drop_duplicates(subset=["hashed_id", "puzzle_name"], keep="last")

df = df.drop_duplicates(subset=["last_written_solution"], keep="last")

stats = df.groupby("puzzle_name").size().sort_values(ascending=False)
puzzles_with_multi_solutions = stats[stats > 1].index.tolist()

df = df[df.puzzle_name.isin(puzzles_with_multi_solutions)]

df = df.rename(columns={"last_written_solution": "description"})

print(f"Number of unique puzzles: {df.puzzle_name.nunique()}")
print(f"Number of solutions: {len(df)}")

df = df[["puzzle_name", "description"]].sort_values(["puzzle_name", "description"])

df.to_csv("data/h_arc_cleaned.csv", index=False)