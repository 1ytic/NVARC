You are an AI specialized in designing and analyzing geometric, physical, and topological puzzles. Your task is to create a Python program that generates an **output grid** based on a puzzle description and **input grid** generation code. Before we begin, please review the following components of the puzzle description:

<puzzle>
{PUZZLE}
</puzzle>

Now, review the generation logic of the input grids:

```python
{INPUT_CODE}
```

Your goal is to create a Python program that generates an output grid for the described puzzle. Use only basic Python commands and the numpy package. The input grid is the initial state, and the output grid is the transformed state after applying the puzzle rules.

First, analyze the puzzle description and provided code step by step, plan the implementation, and outline the structure of your code. Consider the following aspects:

1. Review generation logic
   - Explain how transformation rules can be applied to the generated input grids
   - Highlight useful functions for generating related output grids

2. Constraints and limitations
   - List all constraints and limitations
   - Describe how you'll enforce each constraint in the code

3. Edge cases and potential challenges
   - Identify all potential edge cases or challenges
   - Propose solutions for each identified issue

4. Output grid structure (colors, sizes, shapes, patterns, arrangements)
   - Propose at least two possible grid structures
   - Explain the pros and cons of each structure

5. Implementation steps
   - Outline the main steps of the output grid generation function
   - Propose helper functions and explain their purpose

After your analysis, create the Python program based on your findings. Follow these guidelines:

1. Import numpy and define the main function `generate_puzzle_output`.
2. Implement the output grid generation logic based on your analysis.
3. Output generation logic is deterministic. Do not use random values.
4. Include comments explaining key parts of the code.
5. Print debug information for each critical step. Avoid printing grids, as this complicates debugging. Instead, print extracted information, statistics, or aggregated values. For example, the number of objects found, their properties (shapes, sizes, colors), relationships with other objects (distances, positions), etc.
6. Implement helper functions if needed.
7. Do not implement `main` function or any other entry functions, focus only on the generation logic implementation.
8. Adhere to the following constraints:
   - The maximum size of the 2D grid is 30x30 (height, width).
   - Use only the following 10 colors: 0 - BLACK, 1 - BLUE, 2 - RED, 3 - GREEN, 4 - YELLOW, 5 - GRAY, 6 - MAGENTA, 7 - ORANGE, 8 - SKY, 9 - BROWN.

The following example shows the expected structure of your code:

```python
import numpy as np

def find_vertical_red_line(input_grid: np.ndarray) -> int:
    """Find vertical red line"""
    for x in range(input_grid.shape[1]):
        # Check if there is a red line in the column
        if np.any(input_grid[:, x] == 2):
            return x
    print("No vertical lines")
    return -1

def extend_pattern_from_anchor(output_grid: np.ndarray, pattern: list[int], y: int):
    """Extend complete pattern sequence from anchor point, preserving anchor position"""
    height, width = output_grid.shape
    for i, color in enumerate(pattern):
        x = pattern_start_col + i
        # Check bounds and avoid overwriting reference patterns (top/bottom rows)
        if 0 <= x < width and y != 0 and y != height - 1 and output_grid[y, x] == 0:
            output_grid[y, x] = color

def create_vertical_mirror(input_grid: np.ndarray) -> np.ndarray:
    """Create vertical mirror (flip top-to-bottom) of the input grid"""
    return np.flipud(input_grid)

def generate_puzzle_output(input_grid: np.ndarray) -> np.ndarray:
    """Describe the key insight of this output grid implementation"""

    # Identify output grid size
    height, width = input_grid.shape[0] // 2, input_grid.shape[1] // 3

    # Initialize grid
    output_grid = np.zeros((height, width), dtype=np.int8)

    # Step 1. Find line
    line = find_vertical_red_line(input_grid)
    print(f"Line position: {{line}}")

    # Step 2. Mirror grid
    if line > 5:
         output_grid = create_vertical_mirror(input_grid)
         print("Mirror input grid")

    # Continue implementation here
    ...

    return output_grid
```

Based on your analysis fill in the details of the `generate_puzzle_output` function and create all necessary helper functions. Ensure that you adhere to all specified constraints and incorporate the key elements of the puzzle.