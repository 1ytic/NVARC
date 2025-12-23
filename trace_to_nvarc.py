#!/usr/bin/env python3
"""
Converter: Trelis Trace Format → NVARC Description Format

This module converts Trelis reasoning traces into NVARC-compatible puzzle descriptions
that can be used with the SDG pipeline for synthetic data generation.
"""

import json
import re
from typing import Dict, List


def extract_concepts(observations: List[str], hypotheses: List[str]) -> List[str]:
    """
    Extract puzzle concepts from observations and hypotheses.
    Looks for common ARC concepts like: rotation, mirroring, scaling, tiling, etc.
    """
    concept_keywords = {
        "rotation": ["rotate", "rotated", "rotation", "clockwise", "counterclockwise"],
        "mirroring": ["mirror", "flip", "reflection", "reflected", "horizontally", "vertically"],
        "scaling": ["scale", "scaled", "enlarge", "shrink", "times", "factor"],
        "tiling": ["tile", "tiling", "repeat", "repeated", "pattern"],
        "filling": ["fill", "filled", "flood", "enclosed"],
        "extraction": ["extract", "extracted", "isolate", "separate"],
        "translation": ["move", "shift", "translate", "offset"],
        "color_mapping": ["color", "map", "replace", "substitute"],
        "boundary": ["border", "edge", "boundary", "perimeter"],
        "connected": ["connected", "component", "region", "area"],
    }
    
    found_concepts = set()
    text = " ".join(observations + hypotheses).lower()
    
    for concept, keywords in concept_keywords.items():
        if any(keyword in text for keyword in keywords):
            found_concepts.add(concept)
    
    return sorted(list(found_concepts))


def trace_to_nvarc_description(trace: Dict) -> Dict:
    """
    Convert a Trelis trace to NVARC description format.
    
    Args:
        trace: Trelis trace dictionary with fields:
            - observations: List[str]
            - hypotheses: List[str]
            - rejected_hypotheses: List[Dict]
            - selected_rule: str
            - step_plan: List[str]
            - confidence: float
    
    Returns:
        NVARC description dictionary with fields:
            - rules_summary: str
            - input_generation: str
            - solution_steps: str
            - key_insight: str
            - puzzle_concepts: str
    """
    # Rules summary: Use selected_rule, make it concise
    rules_summary = trace.get("selected_rule", "").strip()
    
    # Solution steps: Convert step_plan list to numbered text
    step_plan = trace.get("step_plan", [])
    if isinstance(step_plan, list):
        solution_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(step_plan)])
    else:
        solution_steps = str(step_plan)
    
    # Key insight: Extract from observations (look for most important pattern)
    observations = trace.get("observations", [])
    if observations:
        # Use first observation as key insight (usually the most fundamental)
        key_insight = observations[0]
    else:
        key_insight = trace.get("selected_rule", "")
    
    # Puzzle concepts: Extract from observations and hypotheses
    hypotheses = trace.get("hypotheses", [])
    puzzle_concepts_list = extract_concepts(observations, hypotheses)
    puzzle_concepts = "\n".join([f"- {concept}" for concept in puzzle_concepts_list])
    
    # Input generation: Infer from task structure
    # For now, use a generic description based on observations
    # This could be enhanced with actual task analysis
    input_generation = "Input grids are provided as examples. The transformation rule must be inferred from the training examples."
    
    # Try to infer input generation from observations
    obs_text = " ".join(observations).lower()
    if "dimensions" in obs_text or "size" in obs_text:
        input_generation = "Input grids of varying sizes are provided. The transformation maintains relationships between input and output dimensions."
    elif "color" in obs_text:
        input_generation = "Input grids contain colored cells. The transformation operates on color patterns and relationships."
    elif "shape" in obs_text or "pattern" in obs_text:
        input_generation = "Input grids contain shapes or patterns. The transformation modifies these patterns according to specific rules."
    
    return {
        "rules_summary": rules_summary,
        "input_generation": input_generation,
        "solution_steps": solution_steps,
        "key_insight": key_insight,
        "puzzle_concepts": puzzle_concepts
    }


def convert_trace_file(trace_file: str, output_file: str = None):
    """
    Convert a trace JSON file to NVARC description format.
    
    Args:
        trace_file: Path to Trelis trace JSON file
        output_file: Optional output path (default: trace_file with .nvarc.md extension)
    """
    with open(trace_file, 'r') as f:
        trace = json.load(f)
    
    nvarc_desc = trace_to_nvarc_description(trace)
    
    if output_file is None:
        output_file = trace_file.replace('.json', '.nvarc.md')
    
    # Format as NVARC-style markdown
    nvarc_text = f"""<rules_summary>
{nvarc_desc["rules_summary"]}
</rules_summary>

<input_generation>
{nvarc_desc["input_generation"]}
</input_generation>

<solution_steps>
{nvarc_desc["solution_steps"]}
</solution_steps>

<key_insight>
{nvarc_desc["key_insight"]}
</key_insight>

<puzzle_concepts>
{nvarc_desc["puzzle_concepts"]}
</puzzle_concepts>
"""
    
    with open(output_file, 'w') as f:
        f.write(nvarc_text)
    
    print(f"Converted {trace_file} → {output_file}")
    return nvarc_desc


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python trace_to_nvarc.py <trace_file.json> [output_file.md]")
        sys.exit(1)
    
    trace_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_trace_file(trace_file, output_file)

