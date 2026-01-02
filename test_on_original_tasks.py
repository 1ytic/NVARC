#!/usr/bin/env python3
"""
Test generated output code on original ARC training tasks.

Loads generated Python code (with generate_puzzle_output function) and tests it
on the original task's training examples to validate quality.
"""
import argparse
import json
import os
import sys
import numpy as np
from pathlib import Path

# Add SDG scripts to path for utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "SDG", "scripts"))
from parser import parse_python_code
from puzzle import execute_code, validate_and_convert_grid

def test_task(task_id, logic_dir="logic", data_dir="arc_agi2_training_only", verbose=False):
    """Test generated output code on original task's training examples."""
    
    # Load original task
    challenges_file = os.path.join(data_dir, "arc-agi_training_challenges.json")
    if not os.path.exists(challenges_file):
        print(f"ERROR: Challenges file not found: {challenges_file}", file=sys.stderr)
        return None
    
    with open(challenges_file, 'r') as f:
        all_tasks = json.load(f)
    
    if task_id not in all_tasks:
        print(f"ERROR: Task {task_id} not found in {challenges_file}", file=sys.stderr)
        return None
    
    task_data = all_tasks[task_id]
    examples = task_data.get("train", [])
    
    if not examples:
        print(f"ERROR: No training examples for task {task_id}", file=sys.stderr)
        return None
    
    # Load generated code
    code_file = os.path.join(logic_dir, f"{task_id}_verified.py")
    if not os.path.exists(code_file):
        # Try without _verified suffix
        code_file = os.path.join(logic_dir, f"{task_id}.py")
        if not os.path.exists(code_file):
            print(f"ERROR: Code file not found: {logic_dir}/{task_id}_verified.py or {task_id}.py", file=sys.stderr)
            return None
    
    with open(code_file, 'r') as f:
        code_content = f.read()
    
    # Verify code has generate_puzzle_output function
    if "def generate_puzzle_output(" not in code_content:
        print(f"ERROR: Code file missing generate_puzzle_output function", file=sys.stderr)
        return None
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Testing Task: {task_id}")
        print(f"{'='*60}")
        print(f"Code file: {code_file}")
        print(f"Training examples: {len(examples)}")
        print()
    
    # Test on each training example
    results = []
    success_count = 0
    
    for i, ex in enumerate(examples):
        inp = np.array(ex["input"], dtype=np.int8)
        target = np.array(ex["output"], dtype=np.int8)
        
        try:
            result = {"input_grid": inp}
            code = code_content + "\noutput_grid = generate_puzzle_output(input_grid)"
            execute_code(code, result, timeout=5)
            pred = validate_and_convert_grid(result.get("output_grid"))
            
            if pred is None:
                status = "FAIL (No output)"
                match = False
                if verbose:
                    print(f"  Example {i+1}: ✗ {status}")
            elif np.array_equal(pred, target):
                status = "SUCCESS"
                match = True
                success_count += 1
                if verbose:
                    print(f"  Example {i+1}: ✓ {status}")
            else:
                status = f"FAIL (Mismatch - expected {target.shape}, got {pred.shape})"
                match = False
                if verbose:
                    print(f"  Example {i+1}: ✗ {status}")
            
            results.append({
                "example_id": i,
                "status": status,
                "match": match,
                "input_shape": inp.shape,
                "target_shape": target.shape,
                "predicted_shape": pred.shape if pred is not None else None
            })
        
        except Exception as e:
            status = f"ERROR ({type(e).__name__}: {str(e)})"
            if verbose:
                print(f"  Example {i+1}: ✗ {status}")
            results.append({
                "example_id": i,
                "status": status,
                "match": False,
                "error": str(e)
            })
    
    total = len(examples)
    success_rate = success_count / total if total > 0 else 0
    
    if verbose:
        print()
        print(f"{'='*60}")
        print(f"Results: {success_count}/{total} examples solved correctly ({success_rate*100:.1f}%)")
        print(f"{'='*60}")
    else:
        print(f"{task_id}: {success_count}/{total} ({success_rate*100:.1f}%)")
    
    return {
        "task_id": task_id,
        "total_examples": total,
        "success_count": success_count,
        "success_rate": success_rate,
        "results": results,
        "passed": success_count == total
    }

def test_batch(logic_dir="logic", data_dir="arc_agi2_training_only", output_file=None, verbose=False):
    """Test all generated code files in logic directory."""
    
    if not os.path.exists(logic_dir):
        print(f"ERROR: Logic directory not found: {logic_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Find all Python files in logic directory
    code_files = list(Path(logic_dir).glob("*.py"))
    if not code_files:
        print(f"ERROR: No Python files found in {logic_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(code_files)} code files to test\n")
    
    all_results = []
    passed_count = 0
    
    for code_file in sorted(code_files):
        # Extract task ID from filename
        task_id = code_file.stem.replace("_verified", "")
        
        result = test_task(task_id, logic_dir, data_dir, verbose=False)
        if result:
            all_results.append(result)
            if result["passed"]:
                passed_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total tasks tested: {len(all_results)}")
    print(f"Tasks with 100% accuracy: {passed_count}/{len(all_results)} ({passed_count/len(all_results)*100:.1f}%)")
    
    # Calculate average success rate
    if all_results:
        avg_success_rate = sum(r["success_rate"] for r in all_results) / len(all_results)
        print(f"Average success rate: {avg_success_rate*100:.1f}%")
    
    # Save results if output file specified
    if output_file:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tasks": len(all_results),
                    "passed_tasks": passed_count,
                    "pass_rate": passed_count / len(all_results) if all_results else 0,
                    "average_success_rate": avg_success_rate if all_results else 0
                },
                "results": all_results
            }, f, indent=2)
        print(f"\nResults saved to: {output_file}")
    
    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test generated output code on original ARC training tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  uv run test_on_original_tasks.py --task 007bbfb7 -v\n"
               "  uv run test_on_original_tasks.py --batch --output results.json"
    )
    parser.add_argument("--task", metavar="ID", help="Test single task ID")
    parser.add_argument("--batch", action="store_true", help="Test all tasks in logic directory")
    parser.add_argument("--logic-dir", default="logic", help="Directory with generated code (default: logic)")
    parser.add_argument("--data-dir", default="arc_agi2_training_only", 
                       help="Directory with ARC training data (default: arc_agi2_training_only)")
    parser.add_argument("--output", metavar="FILE", help="Save results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    if args.task:
        result = test_task(args.task, args.logic_dir, args.data_dir, args.verbose)
        if result:
            sys.exit(0 if result["passed"] else 1)
        else:
            sys.exit(1)
    elif args.batch:
        test_batch(args.logic_dir, args.data_dir, args.output, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)
