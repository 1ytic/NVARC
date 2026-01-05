#!/usr/bin/env python3
"""
Run the complete NVARC SDG pipeline end-to-end.

Simplified pipeline using only SDG prompts:
1. Generate descriptions (.nvarc.md) using summary_v2.md with Gemini 3 Flash
2. [SKIPPED] Task mixing step (mix_v2.md) - we skip this
3. Generate input code using generate_puzzle_input.md with Gemini 3 Flash
4. Generate output code using generate_puzzle_output.md with Gemini 3 Flash
5. Execute input logic to generate input grids
6. Execute output logic to generate output grids
7. Make pairs from input/output grids
8. Build final dataset

Usage:
  python3 run_nvarc_pipeline.py --task-ids 007bbfb7,00d62c1b
  python3 run_nvarc_pipeline.py --all-tasks --count 10
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description, verbose=False):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    if verbose:
        print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=not verbose)

    if result.returncode != 0:
        print(f"ERROR: {description} failed with exit code {result.returncode}", file=sys.stderr)
        if not verbose and result.stderr:
            print(result.stderr.decode(), file=sys.stderr)
        return False

    print(f"✓ {description} completed successfully")
    return True


def check_prerequisites():
    """Check that required files and directories exist."""
    required_files = [
        "SDG/prompts/summary_v2.md",
        "SDG/prompts/generate_puzzle_input.md",
        "SDG/prompts/generate_puzzle_output.md",
        "SDG/scripts/generate_input_grids.py",
        "SDG/scripts/generate_output_grids.py",
        "SDG/scripts/make_pairs.py",
        "SDG/scripts/build_datasets.py",
        "arc_agi2_training_only/arc-agi_training_challenges.json",
        "generate_summaries.py",
        "seed_to_logic.py",
    ]

    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print("ERROR: Missing required files:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        return False

    return True


def run_pipeline(task_ids=None, all_tasks=False, num_tasks=0, num_grids=30, skip_steps=None, verbose=False):
    """Run the complete NVARC SDG pipeline."""

    skip_steps = skip_steps or []

    # Step 1: Generate descriptions (.nvarc.md) using summary_v2.md with Gemini 3 Flash
    if "descriptions" not in skip_steps:
        cmd = ["python3", "generate_summaries.py"]

        if all_tasks:
            cmd.extend(["--all"])
            if num_tasks > 0:
                cmd.extend(["--batch", str(num_tasks)])
        elif task_ids:
            # Process each task ID individually
            for task_id in task_ids:
                task_cmd = cmd + ["--task", task_id]
                if verbose:
                    task_cmd.append("--verbose")
                if not run_command(task_cmd, f"Step 1: Generate Description for {task_id} (summary_v2.md + Gemini 3 Flash)", verbose):
                    return False
            # Skip to step 2 after processing all tasks
        else:
            # Default: process a few tasks
            cmd.extend(["--batch", "3"])

        if not task_ids:  # Only run once if not processing specific tasks
            if verbose:
                cmd.append("--verbose")
            if not run_command(cmd, "Step 1: Generate Descriptions (summary_v2.md + Gemini 3 Flash)", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 1: Generate Descriptions")

    # Step 2: Task mixing - SKIPPED
    print("\n⏭️  Skipping Step 2: Task Mixing (mix_v2.md)")
    print("   We skip task mixing as per requirements")

    # Step 3: Generate input code using generate_puzzle_input.md with Gemini
    # Step 4: Generate output code using generate_puzzle_output.md with Gemini
    if "code_generation" not in skip_steps:
        # Check if we have .nvarc.md files
        nvarc_files = list(Path("traces").glob("*.nvarc.md")) if os.path.exists("traces") else []

        if not nvarc_files:
            print("\n⚠️  No .nvarc.md files found in traces/. Skipping code generation.")
            print("   Run Step 1 first to generate descriptions.")
        else:
            cmd = ["python3", "seed_to_logic.py", "--batch", str(len(nvarc_files))]
            if verbose:
                cmd.append("--verbose")

            if not run_command(cmd, "Step 3-4: Generate Input/Output Code (Gemini 3 Flash)", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 3-4: Generate Input/Output Code")

    # Step 5: Execute input logic to generate grids
    if "input_grids" not in skip_steps:
        # Check if we have logic files
        logic_files = list(Path("logic").glob("*.py")) if os.path.exists("logic") else []

        if not logic_files:
            print("\n⚠️  No logic files found in logic/. Skipping input grid generation.")
            print("   Run Steps 3-4 first to generate code.")
        else:
            # Create output directory structure
            os.makedirs("synthetic/grids_arc_input", exist_ok=True)

            cmd = [
                "python3", "SDG/scripts/generate_input_grids.py",
                "--inputs-mask", "logic/*.py",
                "--grids-prefix", "synthetic/grids_arc_input",
                "--num-grids", str(num_grids)
            ]

            if not run_command(cmd, "Step 5: Execute Input Logic → Generate Input Grids", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 5: Execute Input Logic")

    # Step 6: Execute output logic to generate output grids
    if "output_grids" not in skip_steps:
        if not os.path.exists("synthetic/grids_arc_input"):
            print("\n⚠️  No input grids found. Skipping output grid generation.")
        else:
            cmd = [
                "python3", "SDG/scripts/generate_output_grids.py",
                "--solutions-mask", "logic/*.py",
                "--input-grids-prefix", "synthetic/grids_arc_input",
                "--output-grids-prefix", "synthetic/grids_arc_output",
                "--min-solutions-per-puzzle", "1"
            ]

            if not run_command(cmd, "Step 6: Execute Output Logic → Generate Output Grids", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 6: Execute Output Logic")

    # Step 7: Make pairs
    if "pairs" not in skip_steps:
        if not os.path.exists("synthetic/grids_arc_output"):
            print("\n⚠️  No output grids found. Skipping pair generation.")
        else:
            cmd = [
                "python3", "SDG/scripts/make_pairs.py",
                "--input-grids-prefix", "synthetic/grids_arc_input",
                "--output-grids-mask", "synthetic/grids_arc_output/*/*.json",
                "--output-prefix", "synthetic/pairs_arc",
                "--min-majority-per-grid", "1",
                "--min-pairs-per-puzzle", "5",
                "--min-correct-solutions", "1"
            ]

            if not run_command(cmd, "Step 7: Make Input/Output Pairs", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 7: Make Pairs")

    # Step 8: Build dataset
    if "dataset" not in skip_steps:
        if not os.path.exists("synthetic/pairs_arc"):
            print("\n⚠️  No pairs found. Skipping dataset building.")
        else:
            cmd = [
                "python3", "SDG/scripts/build_datasets.py",
                "--input-prefix", "synthetic/pairs_arc",
                "--output-dataset", "synthetic/arc_dataset.json",
                "--augmentations", "dihedral", "color"
            ]

            if not run_command(cmd, "Step 8: Build Final Dataset", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 8: Build Dataset")

    print(f"\n{'='*60}")
    print("✅ NVARC Pipeline completed successfully!")
    print(f"{'='*60}")
    print("\nGenerated outputs:")
    print("  - traces/          - Puzzle descriptions (.nvarc.md) from summary_v2.md")
    print("  - logic/           - Generated Python code")
    print("  - synthetic/grids_arc_input/   - Input grids")
    print("  - synthetic/grids_arc_output/  - Output grids")
    print("  - synthetic/pairs_arc/         - Input/output pairs")
    print("  - synthetic/arc_dataset.json   - Final dataset")
    print("\nPipeline uses only SDG prompts:")
    print("  - SDG/prompts/summary_v2.md")
    print("  - SDG/prompts/generate_puzzle_input.md")
    print("  - SDG/prompts/generate_puzzle_output.md")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the complete NVARC SDG pipeline (skipping task mixing)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Process specific tasks
  python3 run_nvarc_pipeline.py --task-ids 007bbfb7,00d62c1b

  # Process 10 random tasks
  python3 run_nvarc_pipeline.py --all-tasks --count 10

  # Skip certain steps
  python3 run_nvarc_pipeline.py --skip descriptions,code_generation

  # Generate more grids per task
  python3 run_nvarc_pipeline.py --task-ids 007bbfb7 --num-grids 50
        """
    )
    parser.add_argument("--task-ids", help="Comma-separated task IDs (e.g., 007bbfb7,00d62c1b)")
    parser.add_argument("--all-tasks", action="store_true", help="Process all tasks in ARC-AGI-2 training set")
    parser.add_argument("--count", type=int, default=0, help="Number of tasks to process (with --all-tasks)")
    parser.add_argument("--num-grids", type=int, default=30, help="Number of grids per task (default: 30)")
    parser.add_argument("--skip", help="Comma-separated steps to skip: descriptions,code_generation,input_grids,output_grids,pairs,dataset")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Parse task IDs
    task_ids = None
    if args.task_ids:
        task_ids = [tid.strip() for tid in args.task_ids.split(",")]

    # Parse skip steps
    skip_steps = []
    if args.skip:
        skip_steps = [s.strip() for s in args.skip.split(",")]

    # Run pipeline
    success = run_pipeline(
        task_ids=task_ids,
        all_tasks=args.all_tasks,
        num_tasks=args.count,
        num_grids=args.num_grids,
        skip_steps=skip_steps,
        verbose=args.verbose
    )
    sys.exit(0 if success else 1)
