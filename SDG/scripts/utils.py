import os
import glob
import json
import numpy as np
import re

from matplotlib import colors
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator


cmap = colors.ListedColormap([
    "#000000",
    "#0074D9",
    "#FF4136",
    "#2ECC40",
    "#FFDC00",
    "#AAAAAA",
    "#F012BE",
    "#FF851B",
    "#7FDBFF",
    "#870C25",
])

norm = colors.Normalize(vmin=0, vmax=9)


def plot_array(array, title="example", folder="images/", show=True):
    plt.imshow(array, cmap=cmap, norm=norm)
    ax = plt.gca()
    yticks = list(range(array.shape[0]))
    xticks = list(range(array.shape[1]))
    ax.yaxis.set_major_locator(FixedLocator([y - 0.5 for y in yticks]))
    ax.xaxis.set_major_locator(FixedLocator([x - 0.5 for x in xticks]))
    ax.set_yticklabels(yticks)
    ax.set_xticklabels(xticks)
    ax.set_ylabel("Y")
    ax.set_xlabel("X")
    plt.grid(color="white")
    plt.title(title)
    if show:
        plt.show()
    else:
        plt.savefig(f"{folder}/{title}.png")
    plt.close()


def get_training_puzzle_names():
    training_puzzles = set()
    for file in glob.glob("external/ARC-AGI-2/data/training/*.json"):
        puzzle_name = os.path.basename(file)[:-5]
        training_puzzles.add(puzzle_name)
    return training_puzzles


def recognize_summary(summary: str) -> dict | None:
    match = re.search(r"<rules_summary>\*\*(.*?)\*\*</rules_summary>\*\*.*\*\*<input_generation>\*\*(.*?)\*\*</input_generation>\*\*.*\*\*<solution_steps>\*\*(.*?)\*\*</solution_steps>\*\*.*\*\*<key_insight>\*\*(.*?)\*\*</key_insight>\*\*.*\*\*<puzzle_concepts>\*\*(.*?)\*\*</puzzle_concepts>", summary, re.DOTALL)
    if match:
        return {
            "rules_summary": match.group(1).strip(),
            "input_generation": match.group(2).strip(),
            "solution_steps": match.group(3).strip(),
            "key_insight": match.group(4).strip(),
            "puzzle_concepts": match.group(5).strip()
        }
    match = re.search(r"<rules_summary>(.*?)</rules_summary>.*<input_generation>(.*?)</input_generation>.*<solution_steps>(.*?)</solution_steps>.*<key_insight>(.*?)</key_insight>.*<puzzle_concepts>(.*?)</puzzle_concepts>", summary, re.DOTALL)
    if match:
        return {
            "rules_summary": match.group(1).strip(),
            "input_generation": match.group(2).strip(),
            "solution_steps": match.group(3).strip(),
            "key_insight": match.group(4).strip(),
            "puzzle_concepts": match.group(5).strip()
        }
    return None


def summary_to_text(summary: dict):
    return "\n".join([
        f"<{key}>\n{value}\n</{key}>"
        for key, value in summary.items()
    ])


def read_summaries(folder, puzzle_folder = None):
    data = dict()
    for file_name in glob.glob(f"{folder}/*.md"):
        puzzle_name = os.path.basename(file_name)[:-3]
        if puzzle_folder is not None and os.path.exists(f"{puzzle_folder}/{puzzle_name}/README.md"):
            continue
        with open(file_name, "r") as file:
            summary = file.read().strip()
        summary = recognize_summary(summary)
        if summary is None:
            continue
        data[puzzle_name] = summary
    return data


def read_puzzle(file_name: str) -> tuple[np.ndarray, np.ndarray]:
    with open(file_name, "r") as f:
        data = json.load(f)
    input = np.array(data["input"], dtype=np.int8)
    if "output" in data and "test" not in file_name:
        output = np.array(data["output"], dtype=np.int8)
    else:
        output = None
    return input, output


def convert_grid_to_string(grid: np.ndarray) -> str:
    text = ""
    for row in grid:
        for cell in row:
            text += str(int(cell))
        text += "\n"
    return text.strip()
