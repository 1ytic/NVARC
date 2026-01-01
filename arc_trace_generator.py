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
    if data["trace_source"] != "llm" or data["intended_model_family"] != "gemini-flash":
        raise ValueError("Invalid metadata")
    if not (0.7 <= data["confidence"] <= 0.9):
        raise ValueError(f"Confidence {data['confidence']} out of range [0.7, 0.9]")
    return True

def generate_trace(task_id, task_data, model_name="gemini-2.0-flash-exp"):
    prompt = f"Solve ARC task {task_id}:\n{format_task(task_data, task_id)}\n\nOutput ONLY JSON with keys: task_id, trace_source('llm'), intended_model_family('gemini-flash'), execution_model('{model_name}'), observations(list), hypotheses(list, min 2), rejected_hypotheses(list of {{hypothesis, reason}}), selected_rule(str), step_plan(list), confidence(0.7-0.9). No markdown."
    model = genai.GenerativeModel(model_name)
    res = model.generate_content(prompt).text
    json_text = re.search(r'\{.*\}', res, re.DOTALL).group(0) if '{' in res else res.strip()
    data = json.loads(json_text)
    validate_schema(data)
    data["task_id"] = task_id
    return data

def generate_batch(target_count=100, input_file="arc_agi2_training_only/arc-agi_training_challenges.json", out_dir="traces"):
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
            with open(os.path.join(out_dir, f"{tid}.json"), 'w') as f:
                json.dump(generate_trace(tid, tdata), f, indent=2)
            print(f"Saved {tid}")
            count += 1
            time.sleep(10)
        except Exception as e:
            print(f"Error {tid}: {e}")

if __name__ == "__main__":
    assert_clean_room()
    parser = argparse.ArgumentParser(description="ARC-AGI-2 Trace Generator")
    parser.add_argument("--task", help="Generate trace for single task ID")
    parser.add_argument("--batch", type=int, default=100, help="Generate target number of traces (default: 100)")
    parser.add_argument("--input", default="arc_agi2_training_only/arc-agi_training_challenges.json", help="Input challenges JSON")
    args = parser.parse_args()
    
    if args.task:
        with open(args.input) as f:
            tasks = json.load(f)
        print(json.dumps(generate_trace(args.task, tasks[args.task]), indent=2))
    else:
        generate_batch(target_count=args.batch, input_file=args.input)
