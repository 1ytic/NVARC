import json
import os
import sys
import argparse
import glob

def convert_trace(trace):
    obs, hyps = trace.get("observations", []), trace.get("hypotheses", [])
    concepts = {c for c, kws in {
        "rotation": ["rotate", "mirror", "flip"], "scaling": ["scale", "times", "factor"],
        "tiling": ["tile", "repeat"], "filling": ["fill", "flood"]
    }.items() if any(k in " ".join(obs + hyps).lower() for k in kws)}
    
    desc = {
        "rules_summary": trace.get("selected_rule", ""),
        "input_generation": "Input grids provided; transformation maintains relational scaling." if "times" in str(obs) else "Standard ARC input grids.",
        "solution_steps": "\n".join(f"{i+1}. {s}" for i, s in enumerate(trace.get("step_plan", []))),
        "key_insight": obs[0] if obs else "",
        "puzzle_concepts": "\n".join(f"- {c}" for c in concepts)
    }
    
    sys.path.append(os.path.join(os.path.dirname(__file__), "SDG", "scripts"))
    try:
        from utils import summary_to_text
        return summary_to_text(desc)
    except:
        return "\n".join(f"<{k}>\n{v}\n</{k}>" for k, v in desc.items())

def run_conversion(in_path, out_path):
    files = glob.glob(os.path.join(in_path, "*.json")) if os.path.isdir(in_path) else [in_path]
    for f in files:
        out = out_path or f.replace(".json", ".nvarc.md")
        if os.path.isdir(out): out = os.path.join(out, os.path.basename(f).replace(".json", ".nvarc.md"))
        with open(f) as j, open(out, 'w') as m: m.write(convert_trace(json.load(j)))
        print(f"-> {out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Trelis ARC traces to NVARC")
    parser.add_argument("input", help="Single file or directory")
    parser.add_argument("output", nargs="?", help="Output file or directory")
    args = parser.parse_args()
    run_conversion(args.input, args.output)

