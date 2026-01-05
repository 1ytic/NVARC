#!/usr/bin/env python3
"""
Generate puzzle descriptions using SDG summary_v2.md prompt with Gemini 3 Flash.

This replaces the JSON trace generation method with a direct SDG approach.
Output: .nvarc.md files in the traces/ directory
"""
import argparse
import json
import os
import sys
import time
import google.generativeai as genai
import dotenv
from pathlib import Path

dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def format_grid(grid):
    """Format grid as text."""
    return "\n".join(" ".join(str(c) for c in row) for row in grid) if grid else "[]"


def format_task(task_data, task_id):
    """Format ARC task for the prompt."""
    lines = [f"Task ID: {task_id}", "\nTRAINING EXAMPLES:"]
    for i, ex in enumerate(task_data.get("train", [])):
        lines.extend([
            f"\nExample {i+1}:",
            "Input:",
            format_grid(ex["input"]),
            "Output:",
            format_grid(ex["output"])
        ])
    if task_data.get("test"):
        lines.append("\nTEST EXAMPLES (outputs hidden):")
        for i, ex in enumerate(task_data.get("test", [])):
            lines.extend([
                f"\nTest {i+1}:",
                "Input:",
                format_grid(ex["input"]),
                "(Output: hidden)"
            ])
    return "\n".join(lines)


def read_summary_prompt():
    """Read the summary_v2.md prompt."""
    with open("SDG/prompts/summary_v2.md", 'r') as f:
        return f.read()


def get_example_tasks(num_examples=2):
    """Load a few example tasks for few-shot learning."""
    examples = []
    example_file = "arc_agi2_training_only/arc-agi_training_challenges.json"

    if not os.path.exists(example_file):
        return ""

    with open(example_file) as f:
        tasks = json.load(f)

    # Get a few simple example tasks
    example_ids = list(tasks.keys())[:num_examples]
    for task_id in example_ids:
        puzzle_text = format_task(tasks[task_id], task_id)
        examples.append(f"Example Task:\n{puzzle_text}")

    return "\n\n".join(examples)


def generate_summary(task_id, task_data, model_name="gemini-3-flash-preview", verbose=False):
    """Generate a .nvarc.md summary using SDG summary_v2.md prompt."""
    prompt_template = read_summary_prompt()
    puzzle_text = format_task(task_data, task_id)
    examples = get_example_tasks(num_examples=2)

    # Fill in the prompt template
    prompt = prompt_template.replace("{PUZZLE}", puzzle_text).replace("{EXAMPLES}", examples)

    try:
        if verbose:
            print(f"[{task_id}] Generating summary with {model_name}...", file=sys.stderr)

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        if not response or not hasattr(response, 'text'):
            raise ValueError("No valid response from API")

        summary_text = response.text

        if verbose:
            print(f"[{task_id}] Summary generated (length: {len(summary_text)} chars)", file=sys.stderr)

        return summary_text

    except Exception as e:
        print(f"FAILED {task_id}: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return None


def generate_summaries(target_count=100, input_file="arc_agi2_training_only/arc-agi_training_challenges.json",
                       out_dir="traces", verbose=False):
    """Generate summaries for multiple tasks."""
    os.makedirs(out_dir, exist_ok=True)

    with open(input_file) as f:
        tasks = json.load(f)

    # Check existing files
    existing = {f[:-10] for f in os.listdir(out_dir) if f.endswith('.nvarc.md')}
    count = len(existing)

    if count >= target_count:
        print(f"Goal met ({count}/{target_count}).")
        return

    print(f"Generating {target_count - count} summaries...")

    for task_id, task_data in tasks.items():
        if count >= target_count:
            break
        if task_id in existing:
            continue

        try:
            summary = generate_summary(task_id, task_data, verbose=verbose)

            if summary is None:
                print(f"Skipping {task_id}: Generation failed")
                continue

            # Save as .nvarc.md
            out_path = os.path.join(out_dir, f"{task_id}.nvarc.md")
            with open(out_path, 'w') as f:
                f.write(summary)

            print(f"Saved {task_id}.nvarc.md")
            count += 1

            # Rate limit
            time.sleep(10)

        except Exception as e:
            print(f"Error {task_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment. Check .env file.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Generate puzzle summaries using SDG summary_v2.md prompt with Gemini 3 Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Generate summary for a single task
  python3 generate_summaries.py --task 007bbfb7

  # Generate 100 summaries
  python3 generate_summaries.py --batch 100

  # Generate all tasks
  python3 generate_summaries.py --all"""
    )
    parser.add_argument("--task", help="Generate summary for single task ID")
    parser.add_argument("--batch", type=int, default=100, metavar="N", help="Generate N summaries (default: 100)")
    parser.add_argument("--all", action="store_true", help="Generate summaries for all tasks")
    parser.add_argument("--input", default="arc_agi2_training_only/arc-agi_training_challenges.json",
                        help="Input challenges JSON file")
    parser.add_argument("--output-dir", default="traces", help="Output directory for .nvarc.md files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if args.task:
        # Single task mode
        with open(args.input) as f:
            tasks = json.load(f)

        if args.task not in tasks:
            print(f"ERROR: Task {args.task} not found in {args.input}", file=sys.stderr)
            sys.exit(1)

        summary = generate_summary(args.task, tasks[args.task], verbose=args.verbose)
        if summary:
            os.makedirs(args.output_dir, exist_ok=True)
            out_path = os.path.join(args.output_dir, f"{args.task}.nvarc.md")
            with open(out_path, 'w') as f:
                f.write(summary)
            print(f"Saved {out_path}")
        else:
            print(f"Aborting: Generation failed for {args.task}", file=sys.stderr)
            sys.exit(1)
    else:
        # Batch mode
        target_count = len(json.load(open(args.input))) if args.all else args.batch
        generate_summaries(
            target_count=target_count,
            input_file=args.input,
            out_dir=args.output_dir,
            verbose=args.verbose
        )
