import json
import os
import re
import argparse

def assess_trace(trace):
    obs = trace.get("observations", [])
    hyps = trace.get("hypotheses", [])
    rejs = trace.get("rejected_hypotheses", [])
    
    # 1. Structural (0-1)
    struct = sum([
        len(obs) > 0, len(hyps) >= 2, len(rejs) > 0,
        bool(trace.get("selected_rule", "").strip()),
        len(trace.get("step_plan", [])) > 0,
        0.7 <= trace.get("confidence", 0) <= 0.9
    ]) / 6
    
    # 2. Generalization (Fraction of scale/ratio keywords)
    rel_kws = ["times", "factor", "ratio", "proportional", "relative", "scaled"]
    rel_count = sum(1 for o in obs if any(kw in o.lower() for kw in rel_kws))
    gen = rel_count / max(len(obs), 1)
    
    # 3. Distinctness (Simple set overlap check)
    distinct = 1.0
    if len(hyps) > 1:
        sets = [set(h.lower().split()) for h in hyps]
        overlaps = [len(sets[i] & sets[j]) / max(len(sets[i] | sets[j]), 1) for i in range(len(sets)) for j in range(i+1, len(sets))]
        distinct = 1 - (sum(overlaps) / len(overlaps))
    
    # 4. Consistency (Keyword overlap between rule, plan, observations)
    rule = set(trace.get("selected_rule", "").lower().split())
    plan = set(" ".join(trace.get("step_plan", [])).lower().split())
    obsv = set(" ".join(obs).lower().split())
    cons = (len(rule & plan) / max(len(rule), 1) + len(rule & obsv) / max(len(rule), 1)) / 2 if rule else 0
    
    return {"score": (struct + gen + distinct + cons) / 4, "metrics": {"structural": struct, "generalization": gen, "distinctness": distinct, "consistency": cons}}

def run_assessment(path):
    if os.path.isfile(path):
        with open(path) as f: return {os.path.basename(path): assess_trace(json.load(f))}
    results = {}
    for f in os.listdir(path):
        if f.endswith(".json"):
            with open(os.path.join(path, f)) as j: results[f] = assess_trace(json.load(j))
    if not results: return {"error": "No traces found"}
    avg = sum(r["score"] for r in results.values()) / len(results)
    return {"average_score": avg, "details": results}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARC-AGI-2 Trace Quality Assessor")
    parser.add_argument("path", nargs="?", default="traces", help="Path to trace file or directory (default: traces)")
    args = parser.parse_args()
    print(json.dumps(run_assessment(args.path), indent=2))

