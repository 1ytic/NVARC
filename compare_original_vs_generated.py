#!/usr/bin/env python3
"""
Compare original training examples with generated grids side-by-side.
"""
import json
import sys
import argparse
import numpy as np

# ANSI color codes
COLORS_ANSI = {
    0: '\033[40m \033[0m', 1: '\033[44m \033[0m', 2: '\033[41m \033[0m',
    3: '\033[42m \033[0m', 4: '\033[43m \033[0m', 5: '\033[47m \033[0m',
    6: '\033[45m \033[0m', 7: '\033[48;5;208m \033[0m',
    8: '\033[46m \033[0m', 9: '\033[48;5;94m \033[0m',
}

def format_grid_compact(grid, use_colors=True):
    """Format grid in compact single-line format."""
    if grid is None or (hasattr(grid, 'size') and grid.size == 0) or len(grid) == 0:
        return ""
    
    lines = []
    for row in grid:
        line = ""
        for cell in row:
            if use_colors:
                line += COLORS_ANSI.get(int(cell), '?')
            else:
                line += str(int(cell))
        lines.append(line)
    return lines

def print_comparison(original_ex, generated_pair, orig_num, gen_num, use_colors=True):
    """Print original vs generated side by side."""
    print(f"\n{'='*80}")
    print(f"ORIGINAL Training Example {orig_num}  |  GENERATED Example {gen_num}")
    print(f"{'='*80}")
    
    orig_input = np.array(original_ex.get('input', []))
    orig_output = np.array(original_ex.get('output', []))
    gen_input = generated_pair.get('input', [])
    gen_output = generated_pair.get('output', [])
    
    # Format grids
    orig_input_lines = format_grid_compact(orig_input, use_colors)
    orig_output_lines = format_grid_compact(orig_output, use_colors)
    gen_input_lines = format_grid_compact(gen_input, use_colors)
    gen_output_lines = format_grid_compact(gen_output, use_colors)
    
    max_height = max(len(orig_input_lines), len(gen_input_lines), 
                     len(orig_output_lines), len(gen_output_lines))
    
    print("\n📥 INPUT GRIDS:")
    print("  " + "ORIGINAL".center(35) + " | " + "GENERATED".center(35))
    print("  " + "-" * 35 + " | " + "-" * 35)
    
    for i in range(max_height):
        orig_line = orig_input_lines[i] if i < len(orig_input_lines) else ""
        gen_line = gen_input_lines[i] if i < len(gen_input_lines) else ""
        print(f"  {orig_line:<35} | {gen_line}")
    
    print(f"\n  Original: {orig_input.shape[0]}x{orig_input.shape[1]}  |  Generated: {len(gen_input)}x{len(gen_input[0]) if gen_input else 0}")
    
    print("\n📤 OUTPUT GRIDS:")
    print("  " + "ORIGINAL".center(35) + " | " + "GENERATED".center(35))
    print("  " + "-" * 35 + " | " + "-" * 35)
    
    for i in range(max_height):
        orig_line = orig_output_lines[i] if i < len(orig_output_lines) else ""
        gen_line = gen_output_lines[i] if i < len(gen_output_lines) else ""
        print(f"  {orig_line:<35} | {gen_line}")
    
    print(f"\n  Original: {orig_output.shape[0]}x{orig_output.shape[1]}  |  Generated: {len(gen_output)}x{len(gen_output[0]) if gen_output else 0}")

def main():
    parser = argparse.ArgumentParser(
        description="Compare original training examples vs generated grids side-by-side",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  uv run compare_original_vs_generated.py --task 007bbfb7"
    )
    parser.add_argument("--task", required=True, metavar="ID", help="Task ID")
    parser.add_argument("--data-file", default="arc_agi2_training_only/arc-agi_training_challenges.json", help="Path to training challenges JSON")
    parser.add_argument("--generated-file", default="grids_test/{task}_generated_grids.json", help="Path to generated grids JSON (default: grids_test/{task}_generated_grids.json)")
    parser.add_argument("--numbers", action="store_true", help="Show numbers instead of colors")
    args = parser.parse_args()
    
    # Load original examples
    with open(args.data_file, 'r') as f:
        tasks = json.load(f)
    
    if args.task not in tasks:
        print(f"Error: Task {args.task} not found")
        sys.exit(1)
    
    original_examples = tasks[args.task].get('train', [])
    
    # Load generated grids
    gen_file = args.generated_file.format(task=args.task)
    with open(gen_file, 'r') as f:
        generated_pairs = json.load(f)
    
    print(f"\n📊 Comparison: Original vs Generated for Task {args.task}")
    print(f"Original examples: {len(original_examples)}")
    print(f"Generated examples: {len(generated_pairs)}")
    print("\n💡 Note: Generated grids follow the SAME RULE but are NEW examples")
    print("   They should have similar patterns but different specific grids.\n")
    
    # Compare first original with first generated
    if len(original_examples) > 0 and len(generated_pairs) > 0:
        print_comparison(original_examples[0], generated_pairs[0], 1, 1, use_colors=not args.numbers)
    
    # Show a few more comparisons
    num_comparisons = min(3, len(original_examples), len(generated_pairs))
    for i in range(1, num_comparisons):
        if i < len(original_examples) and i < len(generated_pairs):
            print_comparison(original_examples[i], generated_pairs[i], i+1, i+1, use_colors=not args.numbers)

if __name__ == "__main__":
    main()
