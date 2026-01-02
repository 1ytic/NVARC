#!/usr/bin/env python3
"""
Generate NVARC-style puzzle descriptions from ARC-AGI-2 training tasks.

Uses SDG/prompts/summary_v2.md with Gemini 3 Flash to create structured descriptions
with rules_summary, input_generation, solution_steps, key_insight, and puzzle_concepts.
"""
import argparse
import json
import os
import re
import sys
import time
import google.generativeai as genai
import dotenv
from pathlib import Path

dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def format_grid(grid):
    """Format grid for display in prompt."""
    return "\n".join(" ".join(str(c) for c in r) for r in grid) if grid else "[]"

def format_task_for_prompt(task_data, task_id):
    """Format ARC task into the format expected by summary_v2.md prompt."""
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

def generate_description(task_id, task_data, prompt_template, model_name="gemini-3-flash-preview", verbose=False):
    """Generate NVARC description for a single task using summary_v2.md prompt."""
    try:
        if verbose:
            print(f"[{task_id}] Formatting task for prompt...", file=sys.stderr)
        
        # Format task into puzzle format
        puzzle_text = format_task_for_prompt(task_data, task_id)
        
        # Replace {PUZZLE} placeholder in prompt template
        # Leave {EXAMPLES} empty as we don't have reference examples
        prompt = prompt_template.replace("{PUZZLE}", puzzle_text).replace("{EXAMPLES}", "")
        
        if verbose:
            print(f"[{task_id}] Sending request to Gemini API ({model_name})...", file=sys.stderr)
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        # Extract text from response
        if not hasattr(response, 'text'):
            if hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                    text = ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                else:
                    raise ValueError("Response has no extractable content")
            else:
                raise ValueError("Response has no text attribute and no candidates")
        else:
            text = response.text
        
        if not text or not text.strip():
            raise ValueError("Empty response text from model")
        
        if verbose:
            print(f"[{task_id}] Received response (length: {len(text)} chars)", file=sys.stderr)
        
        # Validate that response has required sections
        required_tags = ["<rules_summary>", "<input_generation>", "<solution_steps>", "<key_insight>", "<puzzle_concepts>"]
        missing_tags = [tag for tag in required_tags if tag not in text]
        if missing_tags:
            print(f"WARNING [{task_id}]: Missing tags: {missing_tags}", file=sys.stderr)
        
        return text.strip()
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"FAILED {task_id}: {error_msg}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return None

def generate_batch(
    target_count=100,
    input_file="arc_agi2_training_only/arc-agi_training_challenges.json",
    out_dir="synthetic/inputs/arc_training/v1/completions",
    prompt_file="SDG/prompts/summary_v2.md",
    model_name="gemini-3-flash-preview",
    verbose=False,
    task_ids=None
):
    """Generate descriptions for multiple tasks."""
    # Load prompt template
    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt file not found: {prompt_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(prompt_file) as f:
        prompt_template = f.read()
    
    # Load tasks
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    with open(input_file) as f:
        tasks = json.load(f)
    
    # Create output directory
    os.makedirs(out_dir, exist_ok=True)
    
    # Check existing descriptions
    existing = {f[:-3] for f in os.listdir(out_dir) if f.endswith('.md')}
    count = len(existing)
    
    if verbose:
        print(f"Found {count} existing descriptions in {out_dir}", file=sys.stderr)
    
    if count >= target_count and not task_ids:
        print(f"Goal met ({count}/{target_count}).")
        return
    
    # Filter tasks if specific IDs provided
    if task_ids:
        tasks_to_process = {tid: tasks[tid] for tid in task_ids if tid in tasks}
        if len(tasks_to_process) < len(task_ids):
            missing = set(task_ids) - set(tasks_to_process.keys())
            print(f"WARNING: Tasks not found: {missing}", file=sys.stderr)
    else:
        tasks_to_process = tasks
    
    # Generate descriptions
    for tid, tdata in tasks_to_process.items():
        if count >= target_count and not task_ids:
            break
        if tid in existing and not task_ids:
            if verbose:
                print(f"Skipping {tid}: Already exists")
            continue
        
        try:
            description = generate_description(tid, tdata, prompt_template, model_name, verbose)
            if description is None:
                print(f"Skipping {tid}: Generation failed")
                continue
            
            # Save description
            out_path = os.path.join(out_dir, f"{tid}.md")
            with open(out_path, 'w') as f:
                f.write(description)
            
            print(f"Saved {tid}")
            count += 1
            
            # Rate limiting - wait 10 seconds between requests
            if count < target_count or task_ids:
                time.sleep(10)
        
        except Exception as e:
            print(f"Error {tid}: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment. Check .env file.", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Generate NVARC puzzle descriptions from ARC-AGI-2 tasks using Gemini 3 Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  uv run generate_descriptions.py --task-ids 007bbfb7,00d62c1b\n"
               "  uv run generate_descriptions.py --batch 100"
    )
    parser.add_argument("--task-ids", help="Comma-separated task IDs to generate (overrides --batch)")
    parser.add_argument("--batch", type=int, default=100, metavar="N", help="Generate N descriptions (default: 100)")
    parser.add_argument("--input", default="arc_agi2_training_only/arc-agi_training_challenges.json", 
                       help="Input challenges JSON file")
    parser.add_argument("--output", default="synthetic/inputs/arc_training/v1/completions",
                       help="Output directory for descriptions")
    parser.add_argument("--prompt", default="SDG/prompts/summary_v2.md",
                       help="Prompt template file")
    parser.add_argument("--model", default="gemini-3-flash-preview",
                       help="Gemini model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Parse task IDs if provided
    task_ids = None
    if args.task_ids:
        task_ids = [tid.strip() for tid in args.task_ids.split(",")]
        print(f"Generating descriptions for {len(task_ids)} specific tasks")
    
    generate_batch(
        target_count=args.batch,
        input_file=args.input,
        out_dir=args.output,
        prompt_file=args.prompt,
        model_name=args.model,
        verbose=args.verbose,
        task_ids=task_ids
    )
