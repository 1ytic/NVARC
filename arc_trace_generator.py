#!/usr/bin/env python3
"""
ARC-AGI-2 Trace Generator (Trelis Fork)

CLEAN-ROOM COMPLIANCE:
- ONLY uses ARC-AGI-2 training challenges from arc_agi2_training_only/
- NO access to solution files (arc-agi_training_solutions.json)
- NO access to test/evaluation challenges or solutions
- NO access to sample submissions
- Only training input/output pairs are visible
- Test outputs are hidden (only inputs shown)
- This is intentional to prevent dataset leakage

FORBIDDEN FILES (will cause immediate exit if detected):
- arc-agi_training_solutions.json
- arc-agi_test_challenges.json
- arc-agi_evaluation_challenges.json
- arc-agi_evaluation_solutions.json
- sample_submission.json
- ARC Prize 2025.zip (or any ARC ZIP archives)
"""

import os
import json
import re
import sys
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ARC task input (multiline string) - for manual input mode
ARC_TASK_TEXT = """
"""

# FORBIDDEN filenames that must NOT exist in workspace
FORBIDDEN_FILENAMES = {
    "arc-agi_training_solutions.json",
    "arc-agi_test_challenges.json",
    "arc-agi_evaluation_challenges.json",
    "arc-agi_evaluation_solutions.json",
    "sample_submission.json",
}

# FORBIDDEN filename patterns (for ZIP archives)
FORBIDDEN_PATTERNS = [
    r".*ARC.*\.zip$",
    r".*arc.*prize.*\.zip$",
]

def assert_clean_room():
    """
    Enforce clean-room compliance by scanning workspace for forbidden files.
    
    This function recursively searches the workspace directory and immediately
    exits with an error if any forbidden filenames or patterns are detected.
    
    This prevents accidental dataset leakage and ensures compliance with
    ARC-AGI-2 and Trelis Fork standards.
    """
    workspace_root = os.path.dirname(os.path.abspath(__file__))
    if not workspace_root:
        workspace_root = os.getcwd()
    
    found_forbidden = []
    
    # Recursively search for forbidden filenames
    for root, dirs, files in os.walk(workspace_root):
        # Skip hidden directories and common build/cache dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for filename in files:
            # Check exact forbidden filenames
            if filename in FORBIDDEN_FILENAMES:
                found_forbidden.append(os.path.join(root, filename))
            
            # Check forbidden patterns
            for pattern in FORBIDDEN_PATTERNS:
                if re.match(pattern, filename, re.IGNORECASE):
                    found_forbidden.append(os.path.join(root, filename))
    
    if found_forbidden:
        error_msg = (
            "CLEAN-ROOM VIOLATION DETECTED\n\n"
            "The following forbidden files were found in the workspace:\n"
        )
        for path in found_forbidden:
            error_msg += f"  - {path}\n"
        error_msg += (
            "\nThis project must NOT contain:\n"
            "  - Solution files (training_solutions, evaluation_solutions)\n"
            "  - Test or evaluation challenge files\n"
            "  - Sample submission files\n"
            "  - ARC Prize ZIP archives\n\n"
            "Please remove these files to ensure clean-room compliance.\n"
            "Only arc_agi2_training_only/arc-agi_training_challenges.json is permitted."
        )
        print(f"ERROR: {error_msg}", file=sys.stderr)
        sys.exit(1)

def format_grid(grid):
    """Format a 2D grid as a readable string for LLM."""
    if not grid:
        return "[]"
    rows = []
    for row in grid:
        rows.append(" ".join(str(cell) for cell in row))
    return "\n".join(rows)

def format_task(task_data, task_id):
    """
    Format ARC task data as text for LLM prompt.
    
    NOTE: Only training examples have input/output pairs.
    Test examples show input only (outputs are hidden).
    Solutions are NOT available - this is intentional to prevent dataset leakage.
    """
    lines = [f"Task ID: {task_id}", ""]
    
    # Training examples (input/output pairs visible)
    lines.append("TRAINING EXAMPLES:")
    for i, example in enumerate(task_data.get("train", [])):
        lines.append(f"\nExample {i+1}:")
        lines.append("Input grid:")
        lines.append(format_grid(example["input"]))
        lines.append("\nOutput grid:")
        lines.append(format_grid(example["output"]))
        lines.append("")
    
    # Test examples (input only, output hidden - solutions not available)
    if task_data.get("test"):
        lines.append("TEST EXAMPLES (solve these - outputs are hidden):")
        for i, example in enumerate(task_data.get("test", [])):
            lines.append(f"\nTest {i+1}:")
            lines.append("Input grid:")
            lines.append(format_grid(example["input"]))
            lines.append("(Output grid: hidden)")
            lines.append("")
    
    return "\n".join(lines)

def extract_json(text):
    """Extract JSON from text, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text.strip()

def validate_schema(data):
    """Validate JSON matches the required schema."""
    required_keys = {
        "task_id", "trace_source", "intended_model_family", "execution_model",
        "observations", "hypotheses", "rejected_hypotheses", "selected_rule",
        "step_plan", "confidence"
    }
    
    if not isinstance(data, dict):
        raise ValueError("Output must be a JSON object")
    
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        raise ValueError(f"Missing required keys: {missing_keys}")
    
    # Type checks
    if not isinstance(data["observations"], list):
        raise ValueError("observations must be a list")
    # Validate observations are plain strings, not objects
    for i, obs in enumerate(data["observations"]):
        if not isinstance(obs, str):
            raise ValueError(f"observations[{i}] must be a plain string, not an object")
    
    if not isinstance(data["hypotheses"], list):
        raise ValueError("hypotheses must be a list")
    if not isinstance(data["rejected_hypotheses"], list):
        raise ValueError("rejected_hypotheses must be a list")
    # Validate rejected_hypotheses structure
    for i, rej in enumerate(data["rejected_hypotheses"]):
        if not isinstance(rej, dict):
            raise ValueError(f"rejected_hypotheses[{i}] must be an object")
        if "hypothesis" not in rej or "reason" not in rej:
            raise ValueError(f"rejected_hypotheses[{i}] must have 'hypothesis' and 'reason' fields")
        if not isinstance(rej["hypothesis"], str) or not isinstance(rej["reason"], str):
            raise ValueError(f"rejected_hypotheses[{i}] 'hypothesis' and 'reason' must be strings")
    if not isinstance(data["step_plan"], list):
        raise ValueError("step_plan must be a list")
    if not isinstance(data["confidence"], (int, float)):
        raise ValueError("confidence must be a number")
    if not isinstance(data["selected_rule"], str):
        raise ValueError("selected_rule must be a string")
    
    # Schema constraints
    if data["trace_source"] != "llm":
        raise ValueError("trace_source must be 'llm'")
    if data["intended_model_family"] != "gemini-flash":
        raise ValueError("intended_model_family must be 'gemini-flash'")
    if data["execution_model"] != "gemini-pro":
        raise ValueError("execution_model must be 'gemini-pro'")
    
    if len(data["hypotheses"]) < 2:
        raise ValueError("Must have at least two hypotheses")
    
    # Confidence range validation
    if data["confidence"] < 0.7 or data["confidence"] > 0.9:
        raise ValueError(f"confidence must be in range [0.7, 0.9], got {data['confidence']}")
    
    return True

def generate_and_save_trace(task_id, task_data, traces_dir="traces"):
    """
    Generate a trace for a task and save it to a file.
    
    Returns True if trace was generated and saved, False if file already exists.
    """
    trace_file = os.path.join(traces_dir, f"{task_id}.json")
    
    # Refuse to overwrite existing traces
    if os.path.exists(trace_file):
        return False
    
    # Generate trace
    data = generate_trace(task_id=task_id, task_data=task_data)
    
    # Save to file
    with open(trace_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True

def generate_trace(task_id=None, task_data=None):
    """Generate structured ARC trace from task."""
    # If task_data is provided, use it; otherwise use ARC_TASK_TEXT
    if task_data and task_id:
        task_text = format_task(task_data, task_id)
    elif ARC_TASK_TEXT.strip():
        task_text = ARC_TASK_TEXT
        task_id = task_id or ""
    else:
        raise ValueError("Either provide task_data and task_id, or set ARC_TASK_TEXT")
    
    prompt = f"""Solve this ARC (Abstraction and Reasoning Corpus) task and generate a structured reasoning trace as JSON.

TASK:
{task_text}

Generate a JSON object with this EXACT structure:
{{
  "task_id": "{task_id}",
  "trace_source": "llm",
  "intended_model_family": "gemini-flash",
  "execution_model": "gemini-pro",
  "observations": [],
  "hypotheses": [],
  "rejected_hypotheses": [],
  "selected_rule": "",
  "step_plan": [],
  "confidence": 0.0
}}

STRICT REQUIREMENTS:

1. observations: Array of plain strings only. Each observation must be:
   - Atomic (one specific pattern)
   - Concrete (directly observable from grids)
   - Derived from grid inspection
   - NO nested objects, NO metadata fields
   - Generalize relationships: State transformations, ratios, or relative patterns rather than absolute sizes
   - AVOID fixed size statements like "input is 2x2" or "output is 6x6"
   - PREFER relational observations like "output dimensions are exactly three times input dimensions" or "output is a 3×3 tiling of input-sized blocks"
   - Only mention absolute sizes if size itself is the transformation rule
   Example: ["Output grid dimensions are exactly 3× the input dimensions.", "The output consists of a 3×3 tiling of blocks matching the input size."]

2. hypotheses: Array of at least TWO meaningfully distinct hypotheses. Each hypothesis must be a string describing a different transformation rule. Avoid redundant paraphrases. If hypotheses are equivalent, rewrite one as a plausible-but-wrong alternative.

3. rejected_hypotheses: Array of objects with "hypothesis" (string) and "reason" (string). Each reason must:
   - Be concrete and specific
   - Reference a specific mismatch with observed data
   - Avoid vague phrases like "does not match"
   Example: {{"hypothesis": "...", "reason": "This produces [[X, Y], [Z, W]] but training example shows [[A, B], [C, D]]"}}

4. selected_rule: String description of the final transformation rule chosen.

5. step_plan: Array of strings describing steps to apply the rule.

6. confidence: Number in range [0.7, 0.9]. Reflect generalization uncertainty, not certainty on seen examples. Do NOT use 1.0.

LANGUAGE STYLE:
- ARC-style reasoning only
- No mention of AI, models, or uncertainty disclaimers
- No verbosity or meta-commentary
- Concise and direct

Output ONLY valid JSON. No markdown, no explanations, no code blocks. Just the JSON object."""

    model = genai.GenerativeModel("gemini-pro-latest")
    response = model.generate_content(prompt)
    
    if not response.text:
        raise ValueError("Empty response from model")
    
    # Extract JSON from response
    json_text = extract_json(response.text)
    
    # Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\nRaw response: {response.text}")
    
    # Validate schema
    validate_schema(data)
    
    # Ensure task_id is set correctly
    data["task_id"] = task_id
    
    return data

def generate_batch(target_count=5):
    """
    Generate a batch of traces, stopping once target_count traces exist.
    Skips tasks that already have saved traces.
    """
    # CONSTRAINT: Only load from ARC-AGI-2 training challenges file
    # DO NOT access: training_solutions, test_challenges, evaluation files
    # This is intentional to prevent dataset leakage
    challenges_file = "arc_agi2_training_only/arc-agi_training_challenges.json"
    if not os.path.exists(challenges_file):
        raise FileNotFoundError(
            f"Training challenges file not found: {challenges_file}\n"
            "NOTE: Only arc-agi_training_challenges.json from arc_agi2_training_only/ is used.\n"
            "Solution files, test challenges, and evaluation data are NOT accessed.\n"
            "This is intentional to ensure clean-room compliance."
        )
    
    # Create traces directory if it doesn't exist
    traces_dir = "traces"
    os.makedirs(traces_dir, exist_ok=True)
    
    # Load all tasks
    with open(challenges_file, 'r') as f:
        all_tasks = json.load(f)
    
    # Count existing traces
    existing_traces = set()
    if os.path.exists(traces_dir):
        for filename in os.listdir(traces_dir):
            if filename.endswith('.json'):
                task_id = filename[:-5]  # Remove .json extension
                existing_traces.add(task_id)
    
    current_count = len(existing_traces)
    
    if current_count >= target_count:
        print(f"Already have {current_count} traces (target: {target_count}), exiting.")
        return
    
    # Iterate through tasks
    for task_id, task_data in all_tasks.items():
        if current_count >= target_count:
            print(f"Reached target of {target_count} traces, exiting.")
            break
        
        # Skip if trace already exists
        if task_id in existing_traces:
            continue
        
        try:
            # Generate and save trace
            if generate_and_save_trace(task_id, task_data, traces_dir):
                current_count += 1
                print(f"Saved trace for task {task_id}")
        except Exception as e:
            print(f"ERROR generating trace for {task_id}: {e}", file=sys.stderr)
            continue

if __name__ == "__main__":
    # ENFORCE CLEAN-ROOM COMPLIANCE: Check for forbidden files before proceeding
    assert_clean_room()
    
    try:
        # Check if task_id provided as command line argument (single task mode)
        if len(sys.argv) > 1:
            task_id = sys.argv[1]
            
            # CONSTRAINT: Only load from ARC-AGI-2 training challenges file
            # DO NOT access: training_solutions, test_challenges, evaluation files
            # This is intentional to prevent dataset leakage
            challenges_file = "arc_agi2_training_only/arc-agi_training_challenges.json"
            if not os.path.exists(challenges_file):
                raise FileNotFoundError(
                    f"Training challenges file not found: {challenges_file}\n"
                    "NOTE: Only arc-agi_training_challenges.json from arc_agi2_training_only/ is used.\n"
                    "Solution files, test challenges, and evaluation data are NOT accessed.\n"
                    "This is intentional to ensure clean-room compliance."
                )
            
            with open(challenges_file, 'r') as f:
                all_tasks = json.load(f)
            
            if task_id not in all_tasks:
                raise ValueError(f"Task ID {task_id} not found in training challenges file")
            
            # Generate trace using only training data (no solutions accessed)
            # This ensures no dataset leakage
            data = generate_trace(task_id=task_id, task_data=all_tasks[task_id])
            print(json.dumps(data, indent=2))
        else:
            # Batch mode: generate up to 5 traces
            generate_batch(target_count=5)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
