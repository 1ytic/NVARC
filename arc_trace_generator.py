"""
ARC-AGI-2 Trace Generator using Gemini 3 Flash.

This script is standalone and does NOT use SDG scripts. It generates JSON traces
directly from ARC task data. SDG scripts are used later in the pipeline:
- trace_to_nvarc.py converts traces to NVARC format
- seed_to_logic.py uses SDG prompts for code generation
"""
import argparse
import time
import os
import json
import re
import sys
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FORBIDDEN_FILES = {"arc-agi_training_solutions.json", "arc-agi_test_challenges.json", "arc-agi_evaluation_challenges.json", "arc-agi_evaluation_solutions.json", "sample_submission.json"}
FORBIDDEN_PATTERNS = [r".*ARC.*\.zip$", r".*arc.*prize.*\.zip$"]

def assert_clean_room():
    """Enforce clean-room compliance by scanning workspace for forbidden files."""
    root_dir = os.path.dirname(os.path.abspath(__file__)) or os.getcwd()
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f in FORBIDDEN_FILES or any(re.match(p, f, re.I) for p in FORBIDDEN_PATTERNS):
                print(f"ERROR: CLEAN-ROOM VIOLATION at {os.path.join(root, f)}", file=sys.stderr)
                sys.exit(1)

def format_grid(grid):
    return "\n".join(" ".join(str(c) for c in r) for r in grid) if grid else "[]"

def format_task(task_data, task_id):
    lines = [f"Task ID: {task_id}", "\nTRAINING EXAMPLES:"]
    for i, ex in enumerate(task_data.get("train", [])):
        lines.extend([f"\nExample {i+1}:", "Input:", format_grid(ex["input"]), "Output:", format_grid(ex["output"])])
    if task_data.get("test"):
        lines.append("\nTEST EXAMPLES (outputs hidden):")
        for i, ex in enumerate(task_data.get("test", [])):
            lines.extend([f"\nTest {i+1}:", "Input:", format_grid(ex["input"]), "(Output: hidden)"])
    return "\n".join(lines)

def validate_schema(data):
    keys = {"task_id", "trace_source", "intended_model_family", "execution_model", "observations", "hypotheses", "rejected_hypotheses", "selected_rule", "step_plan", "confidence"}
    if not isinstance(data, dict) or keys - set(data.keys()):
        raise ValueError(f"Invalid schema: missing {keys - set(data.keys())}")
    if data["trace_source"] != "llm":
        raise ValueError("Invalid metadata")
    if not (0.7 <= data["confidence"] <= 0.9):
        raise ValueError(f"Confidence {data['confidence']} out of range [0.7, 0.9]")
    return True

def generate_trace(task_id, task_data, model_name="gemini-3-flash-preview", verbose=False):
    prompt = f"Solve ARC task {task_id}:\n{format_task(task_data, task_id)}\n\nOutput ONLY JSON with keys: task_id, trace_source('llm'), intended_model_family('gemini-flash'), execution_model('{model_name}'), observations(list), hypotheses(list, min 2), rejected_hypotheses(list of {{hypothesis, reason}}), selected_rule(str), step_plan(list), confidence(0.7-0.9). No markdown."
    try:
        if verbose:
            print(f"[{task_id}] Initializing model {model_name}...", file=sys.stderr)
        model = genai.GenerativeModel(model_name)
        
        if verbose:
            print(f"[{task_id}] Sending request to Gemini API...", file=sys.stderr)
        response = model.generate_content(prompt)
        
        # Check if response was blocked or filtered
        if not response:
            raise ValueError("No response object returned from API")
        
        # Check for safety ratings (blocked content)
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                raise ValueError(f"Response blocked: {response.prompt_feedback.block_reason}")
        
        # Get text from response
        if not hasattr(response, 'text'):
            # Try alternative ways to get text
            if hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                    text = ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                else:
                    raise ValueError("Response has no text attribute and no extractable content")
            else:
                raise ValueError("Response has no text attribute and no candidates")
        else:
            text = response.text
        
        if not text or not text.strip():
            raise ValueError("Empty response text from model")
        
        if verbose:
            print(f"[{task_id}] Received response (length: {len(text)} chars)", file=sys.stderr)
            print(f"[{task_id}] First 200 chars: {text[:200]}", file=sys.stderr)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON found in response. Response: {text[:500]}")
        
        json_text = json_match.group(0)
        if verbose:
            print(f"[{task_id}] Extracted JSON (length: {len(json_text)} chars)", file=sys.stderr)
        
        data = json.loads(json_text)
        validate_schema(data)
        data["task_id"] = task_id
        
        if verbose:
            print(f"[{task_id}] Validation passed, returning trace", file=sys.stderr)
        return data
    except json.JSONDecodeError as e:
        error_msg = f"JSON decode error: {e}. Response text: {text[:500] if 'text' in locals() else 'N/A'}"
        print(f"FAILED {task_id}: {error_msg}", file=sys.stderr)
        return None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"FAILED {task_id}: {error_msg}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return None

def generate_batch(target_count=100, input_file="arc_agi2_training_only/arc-agi_training_challenges.json", out_dir="traces", verbose=False):
    os.makedirs(out_dir, exist_ok=True)
    with open(input_file) as f:
        tasks = json.load(f)
    existing = {f[:-5] for f in os.listdir(out_dir) if f.endswith('.json')}
    count = len(existing)
    if count >= target_count:
        print(f"Goal met ({count}/{target_count}).")
        return
    for tid, tdata in tasks.items():
        if count >= target_count: break
        if tid in existing: continue
        try:
            trace = generate_trace(tid, tdata, verbose=verbose)
            if trace is None:
                print(f"Skipping {tid}: Generation failed")
                continue
            with open(os.path.join(out_dir, f"{tid}.json"), 'w') as f:
                json.dump(trace, f, indent=2)
            print(f"Saved {tid}")
            count += 1
            time.sleep(10)
        except Exception as e:
            print(f"Error {tid}: {e}", file=sys.stderr)

if __name__ == "__main__":
    assert_clean_room()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment. Check .env file.", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Generate ARC-AGI-2 reasoning traces using Gemini 3 Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv run arc_trace_generator.py --task 007bbfb7\n  uv run arc_trace_generator.py --batch 100"
    )
    parser.add_argument("--task", help="Generate trace for single task ID")
    parser.add_argument("--batch", type=int, default=100, metavar="N", help="Generate N traces (default: 100)")
    parser.add_argument("--input", default="arc_agi2_training_only/arc-agi_training_challenges.json", help="Input challenges JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    if args.task:
        with open(args.input) as f:
            tasks = json.load(f)
        if args.task not in tasks:
            print(f"ERROR: Task {args.task} not found in {args.input}", file=sys.stderr)
            sys.exit(1)
        trace = generate_trace(args.task, tasks[args.task], verbose=args.verbose)
        if trace:
            os.makedirs("traces", exist_ok=True)
            with open(f"traces/{args.task}.json", 'w') as f:
                json.dump(trace, f, indent=2)
            print(f"Saved traces/{args.task}.json")
        else:
            print(f"Aborting: Generation failed for {args.task}", file=sys.stderr)
            sys.exit(1)
    else:
        generate_batch(target_count=args.batch, input_file=args.input, verbose=args.verbose)
