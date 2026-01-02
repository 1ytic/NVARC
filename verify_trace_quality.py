#!/usr/bin/env python3
"""
Verify trace quality by:
1. Augmenting the NVARC description (using Gemini 3 Flash)
2. Generating input grids using NVARC input generator
3. Generating transformation program using NVARC output generator
4. Testing the program on original ARC training grids

Only if the program solves ALL original grids is the description considered good.
"""
import os
import json
import argparse
import numpy as np
import google.generativeai as genai
import dotenv
from pathlib import Path
import sys

# Add SDG scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "SDG", "scripts"))
from parser import parse_python_code
from puzzle import execute_code, validate_and_convert_grid

dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3-flash-preview"

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def save_file(path, content):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def extract_code(text):
    import re
    match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1) if match else text

def augment_description(original_desc, model_name=MODEL_NAME):
    """Augment/improve the NVARC description using NVARC summary_v2 prompt (Gemini 3 Flash)."""
    model = genai.GenerativeModel(model_name)
    
    # Use NVARC summary_v2 prompt for augmentation
    try:
        prompt_template = read_file("SDG/prompts/summary_v2.md")
        # Replace {PUZZLE} with original description
        # For examples, we can leave it empty or use a placeholder
        prompt = prompt_template.replace("{PUZZLE}", original_desc).replace("{EXAMPLES}", "")
    except FileNotFoundError:
        # Fallback prompt if summary_v2.md not found
        prompt = f"""You are improving a puzzle description for ARC-AGI. Review the following description and enhance it to be more precise, complete, and clear.

Original description:
{original_desc}

Provide an improved version that:
1. Is more precise about transformation rules
2. Includes all necessary details
3. Is clear enough to generate correct input/output code
4. Maintains the same structure and format

Output the improved description directly, maintaining the same format as the original."""
    
    print(f"[Augment] Improving description with {model_name} using NVARC summary_v2 prompt...")
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, 'text') else ''.join(
        part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')
    )
    return text.strip()

def generate_input_code(description, model_name=MODEL_NAME):
    """Generate input grid generation code using NVARC prompt."""
    model = genai.GenerativeModel(model_name)
    
    prompt_template = read_file("SDG/prompts/generate_puzzle_input.md")
    prompt = prompt_template.replace("{PUZZLE}", description)
    
    print(f"[Input Code] Generating with {model_name}...")
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, 'text') else ''.join(
        part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')
    )
    return extract_code(text)

def generate_output_code(description, input_code, model_name=MODEL_NAME):
    """Generate transformation program using NVARC output prompt."""
    model = genai.GenerativeModel(model_name)
    
    prompt_template = read_file("SDG/prompts/generate_puzzle_output.md")
    prompt = prompt_template.replace("{PUZZLE}", description).replace("{INPUT_CODE}", input_code)
    
    print(f"[Output Code] Generating with {model_name}...")
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, 'text') else ''.join(
        part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')
    )
    return extract_code(text)

def generate_input_grids(input_code, num_grids=5, seed=42):
    """Generate multiple input grids using the input code (NVARC style)."""
    grids = []
    current_seed = seed
    
    for i in range(num_grids * 2):  # Try more to get unique grids
        if len(grids) >= num_grids:
            break
            
        result = {}
        code = input_code + f"\ninput_grid = generate_puzzle_input({current_seed})"
        current_seed += 1
        
        try:
            execute_code(code, result, timeout=5)
            grid = validate_and_convert_grid(result.get("input_grid"))
            if grid:
                # Check for duplicates
                is_duplicate = False
                for existing_grid in grids:
                    if grid == existing_grid:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    grids.append(grid)
        except Exception as e:
            continue
    
    return grids

def generate_output_grids(output_code, input_grids):
    """Generate output grids from input grids using the transformation program."""
    output_grids = []
    
    for input_grid in input_grids:
        try:
            result = {"input_grid": np.array(input_grid, dtype=np.int8)}
            code = output_code + "\noutput_grid = generate_puzzle_output(input_grid)"
            execute_code(code, result, timeout=5)
            output_grid = validate_and_convert_grid(result.get("output_grid"))
            if output_grid:
                output_grids.append(output_grid)
        except Exception as e:
            output_grids.append(None)
    
    return output_grids

def test_on_original_grids(output_code, task_id, data_dir="arc_agi2_training_only"):
    """Test the output code on original ARC training grids."""
    challenges_file = os.path.join(data_dir, "arc-agi_training_challenges.json")
    
    with open(challenges_file, 'r') as f:
        challenge = json.load(f)[task_id]
    
    examples = challenge.get("train", [])
    print(f"\n[Testing] Running on {len(examples)} original training examples...")
    
    success_count = 0
    for i, ex in enumerate(examples):
        inp = np.array(ex["input"], dtype=np.int8)
        target = np.array(ex["output"], dtype=np.int8)
        
        try:
            result = {"input_grid": inp}
            code = output_code + "\noutput_grid = generate_puzzle_output(input_grid)"
            execute_code(code, result, timeout=5)
            pred = validate_and_convert_grid(result.get("output_grid"))
            
            if pred is None:
                print(f"  Example {i+1}: FAIL (No output generated)")
                continue
                
            if np.array_equal(pred, target):
                print(f"  Example {i+1}: ✓ SUCCESS")
                success_count += 1
            else:
                print(f"  Example {i+1}: ✗ FAIL (Mismatch)")
                print(f"    Expected shape: {target.shape}, Got: {pred.shape if pred is not None else 'None'}")
        except Exception as e:
            print(f"  Example {i+1}: ✗ ERROR ({e})")
    
    total = len(examples)
    print(f"\n[Result] {success_count}/{total} examples solved correctly")
    
    if success_count == total:
        print("✅ DESCRIPTION IS GOOD - All original grids solved!")
        return True
    else:
        print("❌ DESCRIPTION NEEDS IMPROVEMENT - Not all grids solved")
        return False

def verify_task(task_id, traces_dir="traces", logic_dir="logic", augmented_dir="traces_augmented", 
                grids_dir="grids_test", data_dir="arc_agi2_training_only", skip_augment=False, num_test_grids=5):
    """Complete verification workflow for a task."""
    print(f"\n{'='*60}")
    print(f"Verifying Task: {task_id}")
    print(f"{'='*60}\n")
    
    # Step 1: Load original NVARC description
    nvarc_file = os.path.join(traces_dir, f"{task_id}.nvarc.md")
    if not os.path.exists(nvarc_file):
        print(f"ERROR: NVARC file not found: {nvarc_file}")
        print("Run: python3 trace_to_nvarc.py traces/")
        return False
    
    original_desc = read_file(nvarc_file)
    print(f"[Step 1] Loaded original description ({len(original_desc)} chars)")
    
    # Step 2: Augment description (optional)
    if skip_augment:
        augmented_desc = original_desc
        print("[Step 2] Skipping augmentation (using original)")
    else:
        augmented_desc = augment_description(original_desc)
        save_file(os.path.join(augmented_dir, f"{task_id}.nvarc.md"), augmented_desc)
        print(f"[Step 2] Augmented description saved ({len(augmented_desc)} chars)")
    
    # Step 3: Generate input code
    input_code = generate_input_code(augmented_desc)
    if not input_code or "def generate_puzzle_input" not in input_code:
        print("ERROR: Failed to generate valid input code")
        return False
    print(f"[Step 3] Generated input code ({len(input_code)} chars)")
    
    # Step 4: Generate output code
    output_code = generate_output_code(augmented_desc, input_code)
    if not output_code or "def generate_puzzle_output" not in output_code:
        print("ERROR: Failed to generate valid output code")
        return False
    print(f"[Step 4] Generated output code ({len(output_code)} chars)")
    
    # Save combined code
    full_code = f"{input_code}\n\n{output_code}"
    save_file(os.path.join(logic_dir, f"{task_id}_verified.py"), full_code)
    print(f"[Saved] Combined code to {logic_dir}/{task_id}_verified.py")
    
    # Step 5: Generate input/output grid pairs (for manual inspection)
    print(f"\n[Step 5] Generating {num_test_grids} input/output grid pairs for manual inspection...")
    input_grids = generate_input_grids(input_code, num_grids=num_test_grids, seed=42)
    print(f"  Generated {len(input_grids)} input grids")
    
    if input_grids:
        output_grids = generate_output_grids(output_code, input_grids)
        print(f"  Generated {len([g for g in output_grids if g is not None])} output grids")
        
        # Save grids for manual inspection
        grids_data = []
        for i, (inp, out) in enumerate(zip(input_grids, output_grids)):
            if out is not None:
                grids_data.append({
                    "pair_id": i,
                    "input": inp,
                    "output": out
                })
        
        grids_file = os.path.join(grids_dir, f"{task_id}_generated_grids.json")
        save_file(grids_file, json.dumps(grids_data, indent=2))
        print(f"  [Saved] Grid pairs to {grids_file}")
        print(f"  [Manual Check] Do these grids look like the original task grids?")
        print(f"    View with: cat {grids_file} | jq '.[0]'")
    else:
        print("  Warning: Could not generate input grids")
    
    # Step 6: Test on original grids
    success = test_on_original_grids(output_code, task_id, data_dir)
    
    return success

def main():
    parser = argparse.ArgumentParser(
        description="Verify trace quality: augment description, generate code, test on original grids",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  uv run verify_trace_quality.py --task 007bbfb7"
    )
    parser.add_argument("--task", required=True, metavar="ID", help="Task ID to verify")
    parser.add_argument("--traces-dir", default="traces", help="Directory with trace files (default: traces)")
    parser.add_argument("--logic-dir", default="logic", help="Directory to save generated code (default: logic)")
    parser.add_argument("--augmented-dir", default="traces_augmented", help="Directory for augmented descriptions (default: traces_augmented)")
    parser.add_argument("--grids-dir", default="grids_test", help="Directory for test grids (default: grids_test)")
    parser.add_argument("--data-dir", default="arc_agi2_training_only", help="Directory with ARC training data (default: arc_agi2_training_only)")
    parser.add_argument("--skip-augment", action="store_true", help="Skip description augmentation step")
    parser.add_argument("--num-test-grids", type=int, default=5, metavar="N", help="Number of test grid pairs to generate (default: 5)")
    args = parser.parse_args()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment", file=sys.stderr)
        sys.exit(1)
    
    success = verify_task(
        args.task,
        traces_dir=args.traces_dir,
        logic_dir=args.logic_dir,
        augmented_dir=args.augmented_dir,
        grids_dir=args.grids_dir,
        data_dir=args.data_dir,
        skip_augment=args.skip_augment,
        num_test_grids=args.num_test_grids
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
