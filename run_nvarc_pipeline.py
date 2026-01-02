#!/usr/bin/env python3
"""
Run the complete NVARC SDG pipeline end-to-end.

This orchestrates all steps:
1. Generate descriptions (summary_v2.md + Gemini 3)
2. Generate input code (generate_puzzle_input.md + Gemini 3)
3. Generate output code (generate_puzzle_output.md + Gemini 3)
4. Execute input grids (SDG/scripts/generate_input_grids.py)
5. Execute output grids (SDG/scripts/generate_output_grids.py)
6. Make pairs (SDG/scripts/make_pairs.py)
7. Test on original tasks (test_on_original_tasks.py)
"""
import argparse
import os
import sys
import subprocess
import json
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
        "arc_agi2_training_only/arc-agi_training_challenges.json",
        "generate_descriptions.py",
        "test_on_original_tasks.py"
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print("ERROR: Missing required files:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        return False
    
    return True

def run_pipeline(task_ids=None, num_grids=30, skip_steps=None, verbose=False):
    """Run the complete NVARC pipeline."""
    
    skip_steps = skip_steps or []
    
    # Step 1: Generate descriptions
    if "descriptions" not in skip_steps:
        cmd = ["uv", "run", "generate_descriptions.py"]
        if task_ids:
            cmd.extend(["--task-ids", ",".join(task_ids)])
        else:
            cmd.extend(["--batch", "100"])
        if verbose:
            cmd.append("--verbose")
        
        if not run_command(cmd, "Step 1: Generate Descriptions", verbose):
            return False
    else:
        print("\n⏭️  Skipping Step 1: Generate Descriptions")
    
    # Step 2: Generate input code (using LLM via SDG scripts)
    # Note: This step is typically done via NeMo-Skills or similar
    # For now, we'll use seed_to_logic.py or similar approach
    if "input_code" not in skip_steps:
        print("\n{'='*60}")
        print("Step 2: Generate Input Code")
        print("{'='*60}")
        print("⚠️  This step requires LLM code generation.")
        print("   Use seed_to_logic.py or NeMo-Skills to generate input code.")
        print("   Expected output: logic/{task_id}_input.py files")
        print("\n   For now, skipping this step - implement as needed.")
    
    # Step 3: Generate output code (using LLM via SDG scripts)
    if "output_code" not in skip_steps:
        print("\n{'='*60}")
        print("Step 3: Generate Output Code")
        print("{'='*60}")
        print("⚠️  This step requires LLM code generation.")
        print("   Use seed_to_logic.py or NeMo-Skills to generate output code.")
        print("   Expected output: logic/{task_id}_verified.py files")
        print("\n   For now, skipping this step - implement as needed.")
    
    # Step 4: Execute input grids
    if "input_grids" not in skip_steps:
        # Check if we have input code files
        logic_files = list(Path("logic").glob("*_input.py")) if os.path.exists("logic") else []
        if not logic_files:
            print("\n⚠️  No input code files found in logic/. Skipping grid generation.")
        else:
            cmd = [
                "python3", "SDG/scripts/generate_input_grids.py",
                "--inputs-mask", "synthetic/inputs/arc_training/v1/completions/*.md",
                "--grids-prefix", "synthetic/grids_arc_input",
                "--num-grids", str(num_grids)
            ]
            
            if not run_command(cmd, "Step 4: Execute Input Grids", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 4: Execute Input Grids")
    
    # Step 5: Execute output grids
    if "output_grids" not in skip_steps:
        # Check if we have output code files
        logic_files = list(Path("logic").glob("*.py")) if os.path.exists("logic") else []
        if not logic_files:
            print("\n⚠️  No code files found in logic/. Skipping output grid generation.")
        else:
            cmd = [
                "python3", "SDG/scripts/generate_output_grids.py",
                "--solutions-mask", "logic/*.py",
                "--input-grids-prefix", "synthetic/grids_arc_input",
                "--output-grids-prefix", "synthetic/grids_arc_output",
                "--min-solutions-per-puzzle", "1"  # We only have 1 solution per task
            ]
            
            if not run_command(cmd, "Step 5: Execute Output Grids", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 5: Execute Output Grids")
    
    # Step 6: Make pairs
    if "pairs" not in skip_steps:
        if not os.path.exists("synthetic/grids_arc_output"):
            print("\n⚠️  No output grids found. Skipping pair generation.")
        else:
            cmd = [
                "python3", "SDG/scripts/make_pairs.py",
                "--input-grids-prefix", "synthetic/grids_arc_input",
                "--output-grids-mask", "synthetic/grids_arc_output/*/*.json",
                "--output-prefix", "synthetic/pairs_arc",
                "--min-majority-per-grid", "1",  # Adjusted for single solution
                "--min-pairs-per-puzzle", "5",   # At least 5 valid pairs
                "--min-correct-solutions", "1"   # We only have 1 solution
            ]
            
            if not run_command(cmd, "Step 6: Make Pairs", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 6: Make Pairs")
    
    # Step 7: Test on original tasks
    if "test" not in skip_steps:
        if not os.path.exists("logic"):
            print("\n⚠️  No logic directory found. Skipping testing.")
        else:
            cmd = [
                "uv", "run", "test_on_original_tasks.py",
                "--batch",
                "--output", "test_results.json"
            ]
            if verbose:
                cmd.append("--verbose")
            
            if not run_command(cmd, "Step 7: Test on Original Tasks", verbose):
                return False
    else:
        print("\n⏭️  Skipping Step 7: Test on Original Tasks")
    
    print(f"\n{'='*60}")
    print("✅ Pipeline completed successfully!")
    print(f"{'='*60}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the complete NVARC SDG pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  uv run run_nvarc_pipeline.py --task-ids 007bbfb7,00d62c1b\n"
               "  uv run run_nvarc_pipeline.py --skip descriptions,input_code,output_code"
    )
    parser.add_argument("--task-ids", help="Comma-separated task IDs (optional)")
    parser.add_argument("--num-grids", type=int, default=30, help="Number of grids per task (default: 30)")
    parser.add_argument("--skip", help="Comma-separated steps to skip: descriptions,input_code,output_code,input_grids,output_grids,pairs,test")
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
    success = run_pipeline(task_ids, args.num_grids, skip_steps, args.verbose)
    sys.exit(0 if success else 1)
