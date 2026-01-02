import os
import json
import time
import argparse
import google.generativeai as genai
import dotenv
from pathlib import Path

dotenv.load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def read_file(path):
    with open(path, 'r') as f: return f.read()

def save_file(path, content):
    with open(path, 'w') as f: f.write(content)

def extract_code(text):
    import re
    match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
    return match.group(1) if match else text

def generate_logic(task_id, description, model_name="gemini-3-flash-preview"):
    model = genai.GenerativeModel(model_name)
    
    # 1. Generate Input Code
    input_prompt = read_file("SDG/prompts/generate_puzzle_input.md").replace("{PUZZLE}", description)
    print(f"[{task_id}] Generating input logic...")
    input_res = model.generate_content(input_prompt).text
    input_code = extract_code(input_res)
    
    # 2. Generate Output Code
    output_prompt = read_file("SDG/prompts/generate_puzzle_output.md").replace("{PUZZLE}", description).replace("{INPUT_CODE}", input_code)
    print(f"[{task_id}] Generating output logic...")
    output_res = model.generate_content(output_prompt).text
    output_code = extract_code(output_res)
    
    # Combine (NVARC expects both in one file or handled by scripts)
    # We'll save them as task_id.py containing both functions
    full_code = f"{input_code}\n\n{output_code}"
    return full_code

def main():
    parser = argparse.ArgumentParser(
        description="Generate Python logic from NVARC descriptions using Gemini 3 Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  uv run seed_to_logic.py --batch 3"
    )
    parser.add_argument("--batch", type=int, default=100, metavar="N", help="Target number of logic files (default: 100)")
    parser.add_argument("--input-dir", default="traces", help="Directory with .nvarc.md files (default: traces)")
    parser.add_argument("--output-dir", default="logic", help="Directory to save .py files (default: logic)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    seeds = list(Path(args.input_dir).glob("*.nvarc.md"))
    
    count = 0
    for seed_path in seeds:
        if count >= args.batch: break
        task_id = seed_path.stem.split('.')[0]
        out_path = os.path.join(args.output_dir, f"{task_id}.py")
        
        if os.path.exists(out_path): continue
        
        try:
            desc = read_file(seed_path)
            code = generate_logic(task_id, desc)
            save_file(out_path, code)
            count += 1
            time.sleep(10) # Rate limit
        except Exception as e:
            print(f"Error {task_id}: {e}")

if __name__ == "__main__":
    main()
