#!/usr/bin/env python3
"""
Visualize generated grids in ARC-AGI style format.
"""
import json
import sys
import argparse

# ANSI color codes for terminal
COLORS_ANSI = {
    0: '\033[40m \033[0m',  # BLACK - black background
    1: '\033[44m \033[0m',  # BLUE - blue background
    2: '\033[41m \033[0m',  # RED - red background
    3: '\033[42m \033[0m',  # GREEN - green background
    4: '\033[43m \033[0m',  # YELLOW - yellow background
    5: '\033[47m \033[0m',  # GRAY - white/gray background
    6: '\033[45m \033[0m',  # MAGENTA - magenta background
    7: '\033[48;5;208m \033[0m',  # ORANGE - orange (closest ANSI)
    8: '\033[46m \033[0m',  # SKY - cyan background
    9: '\033[48;5;94m \033[0m',  # BROWN - brown (closest ANSI)
}

COLOR_NAMES = {
    0: 'BLACK', 1: 'BLUE', 2: 'RED', 3: 'GREEN', 4: 'YELLOW',
    5: 'GRAY', 6: 'MAGENTA', 7: 'ORANGE', 8: 'SKY', 9: 'BROWN'
}

def format_grid_visual(grid, use_colors=True, label="", show_border=True):
    """Format a grid with visual representation."""
    if not grid:
        return "Empty grid"
    
    lines = []
    if label:
        lines.append(f"  {label}")
        lines.append("")
    
    height = len(grid)
    width = len(grid[0]) if grid else 0
    
    if show_border:
        lines.append("  " + "┌" + "─" * (width * 2 + 1) + "┐")
    
    for i, row in enumerate(grid):
        if show_border:
            line = "  │ "
        else:
            line = "  "
        
        for cell in row:
            if use_colors:
                line += COLORS_ANSI.get(cell, '?') + " "
            else:
                line += str(cell) + " "
        
        if show_border:
            line += "│"
        lines.append(line)
    
    if show_border:
        lines.append("  " + "└" + "─" * (width * 2 + 1) + "┘")
    
    return '\n'.join(lines)

def format_grid_compact(grid, use_colors=True):
    """Format grid in compact format (no borders)."""
    if not grid:
        return "Empty"
    
    lines = []
    for row in grid:
        line = ""
        for cell in row:
            if use_colors:
                line += COLORS_ANSI.get(cell, '?')
            else:
                line += str(cell)
        lines.append("  " + line)
    
    return '\n'.join(lines)

def print_example_pair(pair, pair_id, use_colors=True, compact=False):
    """Print input/output pair in ARC-AGI style."""
    print(f"\n{'='*70}")
    print(f"Example {pair_id + 1}")
    print(f"{'='*70}")
    
    input_grid = pair.get('input', [])
    output_grid = pair.get('output', [])
    
    if compact:
        # Side-by-side compact view
        print("\n  INPUT ({}x{})                    OUTPUT ({}x{})".format(
            len(input_grid), len(input_grid[0]) if input_grid else 0,
            len(output_grid), len(output_grid[0]) if output_grid else 0
        ))
        print("  " + "-" * 30 + "    " + "-" * 30)
        
        # Print grids side by side
        max_height = max(len(input_grid), len(output_grid))
        for i in range(max_height):
            input_line = ""
            if i < len(input_grid):
                for cell in input_grid[i]:
                    input_line += COLORS_ANSI.get(cell, '?') if use_colors else str(cell)
            else:
                input_line = " " * len(input_grid[0]) if input_grid else ""
            
            output_line = ""
            if i < len(output_grid):
                for cell in output_grid[i]:
                    output_line += COLORS_ANSI.get(cell, '?') if use_colors else str(cell)
            else:
                output_line = " " * len(output_grid[0]) if output_grid else ""
            
            print(f"  {input_line:<30}    {output_line}")
    else:
        # Stacked view (like ARC interface)
        print("\n📥 INPUT GRID:")
        print(format_grid_visual(input_grid, use_colors, show_border=True))
        
        if input_grid:
            colors = set()
            for row in input_grid:
                colors.update(row)
            print(f"\n  Size: {len(input_grid)}x{len(input_grid[0])}")
            print(f"  Colors: {sorted(colors)}")
        
        print("\n📤 OUTPUT GRID:")
        print(format_grid_visual(output_grid, use_colors, show_border=True))
        
        if output_grid:
            colors = set()
            for row in output_grid:
                colors.update(row)
            print(f"\n  Size: {len(output_grid)}x{len(output_grid[0])}")
            print(f"  Colors: {sorted(colors)}")

def main():
    parser = argparse.ArgumentParser(
        description="Visualize generated grids in ARC-AGI style",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv run view_grids_visual.py grids_test/007bbfb7_generated_grids.json\n  uv run view_grids_visual.py grids_test/007bbfb7_generated_grids.json --all"
    )
    parser.add_argument("file", help="JSON file with grid pairs")
    parser.add_argument("--pair", type=int, metavar="N", help="Show only specific pair (0-indexed)")
    parser.add_argument("--numbers", action="store_true", help="Show numbers instead of colors")
    parser.add_argument("--all", action="store_true", help="Show all pairs")
    parser.add_argument("--compact", action="store_true", help="Show side-by-side compact view")
    args = parser.parse_args()
    
    with open(args.file, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("Error: Expected a list of grid pairs")
        sys.exit(1)
    
    print(f"\n📊 ARC-AGI Grid Visualization")
    print(f"Found {len(data)} example pair(s)")
    print("\nColor Legend:")
    for num, name in COLOR_NAMES.items():
        if args.numbers:
            print(f"  {num} = {name}")
        else:
            color_block = COLORS_ANSI.get(num, '?')
            print(f"  {color_block} = {name} ({num})")
    
    if args.pair is not None:
        if 0 <= args.pair < len(data):
            print_example_pair(data[args.pair], args.pair, use_colors=not args.numbers, compact=args.compact)
        else:
            print(f"Error: Pair {args.pair} not found (available: 0-{len(data)-1})")
            sys.exit(1)
    elif args.all:
        for i, pair in enumerate(data):
            print_example_pair(pair, i, use_colors=not args.numbers, compact=args.compact)
            if i < len(data) - 1:
                print("\n")
    else:
        # Show first pair by default
        print("\n💡 Tip: Use --all to see all pairs, --pair N for specific pair, --compact for side-by-side")
        print_example_pair(data[0], 0, use_colors=not args.numbers, compact=args.compact)

if __name__ == "__main__":
    main()
