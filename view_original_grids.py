#!/usr/bin/env python3
"""
View the original ARC training examples from the task data.
"""
import json
import sys
import argparse
import numpy as np

# ANSI color codes
COLORS_ANSI = {
    0: '\033[40m \033[0m',  # BLACK
    1: '\033[44m \033[0m',  # BLUE
    2: '\033[41m \033[0m',  # RED
    3: '\033[42m \033[0m',  # GREEN
    4: '\033[43m \033[0m',  # YELLOW
    5: '\033[47m \033[0m',  # GRAY
    6: '\033[45m \033[0m',  # MAGENTA
    7: '\033[48;5;208m \033[0m',  # ORANGE
    8: '\033[46m \033[0m',  # SKY
    9: '\033[48;5;94m \033[0m',  # BROWN
}

COLOR_NAMES = {
    0: 'BLACK', 1: 'BLUE', 2: 'RED', 3: 'GREEN', 4: 'YELLOW',
    5: 'GRAY', 6: 'MAGENTA', 7: 'ORANGE', 8: 'SKY', 9: 'BROWN'
}

def format_grid_visual(grid, use_colors=True):
    """Format a grid with visual representation."""
    if grid is None or (hasattr(grid, 'size') and grid.size == 0) or len(grid) == 0:
        return "Empty grid"
    
    lines = []
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    lines.append("  " + "┌" + "─" * (width * 2 + 1) + "┐")
    
    for row in grid:
        line = "  │ "
        for cell in row:
            if use_colors:
                line += COLORS_ANSI.get(int(cell), '?') + " "
            else:
                line += str(int(cell)) + " "
        line += "│"
        lines.append(line)
    
    lines.append("  " + "└" + "─" * (width * 2 + 1) + "┘")
    
    return '\n'.join(lines)

def print_training_example(ex, ex_num, use_colors=True):
    """Print a training example."""
    print(f"\n{'='*70}")
    print(f"Training Example {ex_num}")
    print(f"{'='*70}")
    
    input_grid = np.array(ex.get('input', []))
    output_grid = np.array(ex.get('output', []))
    
    print("\n📥 INPUT GRID:")
    print(format_grid_visual(input_grid, use_colors))
    
    if len(input_grid) > 0:
        colors = set(input_grid.flatten())
        print(f"\n  Size: {input_grid.shape[0]}x{input_grid.shape[1]}")
        print(f"  Colors: {sorted([int(c) for c in colors])}")
    
    print("\n📤 OUTPUT GRID:")
    print(format_grid_visual(output_grid, use_colors))
    
    if len(output_grid) > 0:
        colors = set(output_grid.flatten())
        print(f"\n  Size: {output_grid.shape[0]}x{output_grid.shape[1]}")
        print(f"  Colors: {sorted([int(c) for c in colors])}")

def main():
    parser = argparse.ArgumentParser(
        description="View original ARC training examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  uv run view_original_grids.py --task 007bbfb7"
    )
    parser.add_argument("--task", required=True, metavar="ID", help="Task ID")
    parser.add_argument("--data-file", default="arc_agi2_training_only/arc-agi_training_challenges.json", 
                       help="Path to training challenges JSON (default: arc_agi2_training_only/arc-agi_training_challenges.json)")
    parser.add_argument("--example", type=int, metavar="N", help="Show only specific example (1-indexed)")
    parser.add_argument("--numbers", action="store_true", help="Show numbers instead of colors")
    args = parser.parse_args()
    
    with open(args.data_file, 'r') as f:
        tasks = json.load(f)
    
    if args.task not in tasks:
        print(f"Error: Task {args.task} not found in {args.data_file}")
        sys.exit(1)
    
    task_data = tasks[args.task]
    examples = task_data.get('train', [])
    
    print(f"\n📊 Original Training Examples for Task: {args.task}")
    print(f"Found {len(examples)} training example(s)")
    print("\nColor Legend:")
    for num, name in COLOR_NAMES.items():
        if args.numbers:
            print(f"  {num} = {name}")
        else:
            color_block = COLORS_ANSI.get(num, '?')
            print(f"  {color_block} = {name} ({num})")
    
    if args.example is not None:
        if 1 <= args.example <= len(examples):
            print_training_example(examples[args.example - 1], args.example, use_colors=not args.numbers)
        else:
            print(f"Error: Example {args.example} not found (available: 1-{len(examples)})")
            sys.exit(1)
    else:
        # Show all examples
        for i, ex in enumerate(examples, 1):
            print_training_example(ex, i, use_colors=not args.numbers)
            if i < len(examples):
                print("\n")

if __name__ == "__main__":
    main()
