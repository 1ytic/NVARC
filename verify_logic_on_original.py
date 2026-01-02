import os
import json
import importlib.util
import numpy as np

def load_module(file_path):
    spec = importlib.util.spec_from_file_location("logic_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verify_task(task_id, logic_dir="logic", data_dir="arc_agi2_training_only"):
    print(f"\n--- Verifying Task {task_id} ---")
    with open(os.path.join(data_dir, "arc-agi_training_challenges.json")) as f:
        challenge = json.load(f)[task_id]
    logic_file = os.path.join(logic_dir, f"{task_id}.py")
    if not os.path.exists(logic_file):
        print(f"Logic file not found: {logic_file}")
        return False
    module = load_module(logic_file)
    if not hasattr(module, "generate_puzzle_output"):
        print("Missing generate_puzzle_output")
        return False
    examples = challenge.get("train", [])
    success_count = 0
    for i, ex in enumerate(examples):
        inp, target = np.array(ex["input"], dtype=np.int8), np.array(ex["output"], dtype=np.int8)
        try:
            pred = module.generate_puzzle_output(inp)
            if np.array_equal(pred, target):
                print(f"Example {i+1}: SUCCESS")
                success_count += 1
            else:
                print(f"Example {i+1}: FAIL (Mismatch)")
        except Exception as e:
            print(f"Example {i+1}: ERROR ({e})")
    print(f"Final Result: {success_count}/{len(examples)} solved")
    return success_count == len(examples)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Verify generated logic code against original ARC training grids",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  uv run verify_logic_on_original.py --task 007bbfb7\n  uv run verify_logic_on_original.py --task 007bbfb7 --logic-dir logic"
    )
    parser.add_argument("--task", required=True, metavar="ID", help="Task ID to verify")
    parser.add_argument("--logic-dir", default="logic", help="Directory with generated .py files (default: logic)")
    parser.add_argument("--data-dir", default="arc_agi2_training_only", help="Directory with ARC training data (default: arc_agi2_training_only)")
    args = parser.parse_args()
    success = verify_task(args.task, logic_dir=args.logic_dir, data_dir=args.data_dir)
    exit(0 if success else 1)
