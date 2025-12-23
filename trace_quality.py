#!/usr/bin/env python3
"""
Trace Quality Assessment Module

Evaluates the quality of ARC-AGI-2 reasoning traces across multiple dimensions:
- Structural completeness
- Content quality
- Generalization
- Consistency
"""

import json
import os
import re
from typing import Dict, List, Tuple
from collections import Counter


def assess_structural_quality(trace: Dict) -> Dict[str, bool]:
    """Assess structural completeness of trace."""
    checks = {
        "has_observations": len(trace.get("observations", [])) > 0,
        "has_multiple_hypotheses": len(trace.get("hypotheses", [])) >= 2,
        "has_rejected_hypotheses": len(trace.get("rejected_hypotheses", [])) > 0,
        "has_selected_rule": bool(trace.get("selected_rule", "").strip()),
        "has_step_plan": len(trace.get("step_plan", [])) > 0,
        "confidence_in_range": 0.7 <= trace.get("confidence", 0) <= 0.9,
        "observations_are_strings": all(isinstance(obs, str) for obs in trace.get("observations", [])),
    }
    return checks


def assess_generalization_quality(trace: Dict) -> Dict[str, any]:
    """Assess generalization quality (relational vs absolute observations)."""
    observations = trace.get("observations", [])
    
    # Count absolute vs relational observations
    absolute_keywords = ["2x2", "3x3", "6x6", "always", "is always", "exactly"]
    relational_keywords = ["times", "factor", "ratio", "proportional", "relative", "scaled"]
    
    absolute_count = sum(1 for obs in observations if any(kw in obs.lower() for kw in absolute_keywords))
    relational_count = sum(1 for obs in observations if any(kw in obs.lower() for kw in relational_keywords))
    
    # Check for example-specific sizes
    has_absolute_sizes = any(
        re.search(r'\d+x\d+', obs.lower()) and not any(rel_kw in obs.lower() for rel_kw in relational_keywords)
        for obs in observations
    )
    
    return {
        "absolute_observations": absolute_count,
        "relational_observations": relational_count,
        "has_absolute_sizes": has_absolute_sizes,
        "generalization_score": relational_count / max(len(observations), 1),
    }


def assess_hypothesis_quality(trace: Dict) -> Dict[str, any]:
    """Assess quality of hypotheses and rejections."""
    hypotheses = trace.get("hypotheses", [])
    rejected = trace.get("rejected_hypotheses", [])
    
    # Check if hypotheses are distinct (simple word overlap check)
    hypothesis_texts = [h.lower() for h in hypotheses]
    distinctness_scores = []
    for i, h1 in enumerate(hypothesis_texts):
        for j, h2 in enumerate(hypothesis_texts):
            if i < j:
                # Simple word overlap
                words1 = set(h1.split())
                words2 = set(h2.split())
                overlap = len(words1 & words2) / max(len(words1 | words2), 1)
                distinctness_scores.append(1 - overlap)  # Higher = more distinct
    
    avg_distinctness = sum(distinctness_scores) / max(len(distinctness_scores), 1)
    
    # Check rejection quality
    rejection_quality = []
    for rej in rejected:
        reason = rej.get("reason", "")
        # Check if reason is concrete (has specific details)
        has_specifics = any(
            keyword in reason.lower()
            for keyword in ["example", "shows", "produces", "actual", "training", "would produce"]
        )
        rejection_quality.append(has_specifics)
    
    return {
        "num_hypotheses": len(hypotheses),
        "num_rejected": len(rejected),
        "avg_hypothesis_distinctness": avg_distinctness,
        "rejection_quality_score": sum(rejection_quality) / max(len(rejection_quality), 1),
        "has_concrete_rejections": all(rejection_quality),
    }


def assess_consistency(trace: Dict) -> Dict[str, bool]:
    """Assess internal consistency of trace."""
    selected_rule = trace.get("selected_rule", "").lower()
    step_plan = " ".join(trace.get("step_plan", [])).lower()
    observations = " ".join(trace.get("observations", [])).lower()
    
    # Check if step_plan aligns with selected_rule
    rule_keywords = set(selected_rule.split())
    plan_keywords = set(step_plan.split())
    rule_plan_overlap = len(rule_keywords & plan_keywords) / max(len(rule_keywords), 1)
    
    # Check if observations support selected rule
    obs_keywords = set(observations.split())
    rule_obs_overlap = len(rule_keywords & obs_keywords) / max(len(rule_keywords), 1)
    
    return {
        "rule_plan_alignment": rule_plan_overlap > 0.3,
        "rule_observations_alignment": rule_obs_overlap > 0.2,
        "rule_plan_overlap_score": rule_plan_overlap,
        "rule_observations_overlap_score": rule_obs_overlap,
    }


def assess_trace(trace: Dict) -> Dict:
    """Comprehensive quality assessment of a trace."""
    return {
        "structural": assess_structural_quality(trace),
        "generalization": assess_generalization_quality(trace),
        "hypotheses": assess_hypothesis_quality(trace),
        "consistency": assess_consistency(trace),
    }


def assess_trace_file(trace_file: str) -> Dict:
    """Assess quality of a trace JSON file."""
    with open(trace_file, 'r') as f:
        trace = json.load(f)
    return assess_trace(trace)


def assess_trace_directory(traces_dir: str = "traces") -> Dict:
    """Assess all traces in a directory."""
    results = {}
    scores = []
    
    for filename in os.listdir(traces_dir):
        if filename.endswith('.json'):
            trace_file = os.path.join(traces_dir, filename)
            task_id = filename[:-5]  # Remove .json
            assessment = assess_trace_file(trace_file)
            results[task_id] = assessment
            
            # Calculate overall score
            structural_score = sum(assessment["structural"].values()) / len(assessment["structural"])
            gen_score = assessment["generalization"]["generalization_score"]
            hyp_score = assessment["hypotheses"]["avg_hypothesis_distinctness"]
            cons_score = (
                assessment["consistency"]["rule_plan_overlap_score"] +
                assessment["consistency"]["rule_observations_overlap_score"]
            ) / 2
            
            overall_score = (structural_score + gen_score + hyp_score + cons_score) / 4
            scores.append(overall_score)
    
    return {
        "individual_assessments": results,
        "average_score": sum(scores) / len(scores) if scores else 0,
        "num_traces": len(results),
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Assess single file
        trace_file = sys.argv[1]
        assessment = assess_trace_file(trace_file)
        print(json.dumps(assessment, indent=2))
    else:
        # Assess directory
        results = assess_trace_directory()
        print(json.dumps(results, indent=2))

