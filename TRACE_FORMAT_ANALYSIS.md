# Trace Format Analysis: Trelis vs NVARC

## Current Trelis Trace Format (v1)

Our traces capture **reasoning process**:
```json
{
  "task_id": "...",
  "trace_source": "llm",
  "intended_model_family": "gemini-flash",
  "execution_model": "gemini-pro",
  "observations": ["pattern1", "pattern2"],  // What was noticed
  "hypotheses": ["hypothesis1", "hypothesis2"],  // Alternatives considered
  "rejected_hypotheses": [{"hypothesis": "...", "reason": "..."}],  // Why alternatives failed
  "selected_rule": "...",  // Final chosen rule
  "step_plan": ["step1", "step2"],  // How to apply rule
  "confidence": 0.8
}
```

## NVARC Description Format

NVARC uses **puzzle descriptions** for code generation:
```json
{
  "rules_summary": "...",  // Concise overview
  "input_generation": "...",  // How to generate inputs
  "solution_steps": "...",  // How to solve
  "key_insight": "...",  // Main idea
  "puzzle_concepts": ["concept1", "concept2"]  // Required concepts
}
```

## Key Differences

1. **Purpose**: 
   - Trelis traces = reasoning process (how someone thinks)
   - NVARC descriptions = puzzle specification (how to generate/solve)

2. **Structure**:
   - Trelis includes rejected hypotheses (shows reasoning)
   - NVARC focuses on final solution only

3. **Usage**:
   - Trelis traces → quality assessment, comparison with human traces
   - NVARC descriptions → code generation pipeline

## Alignment Strategy

**Option A**: Convert Trelis traces → NVARC descriptions
- Map `selected_rule` → `rules_summary`
- Map `step_plan` → `solution_steps`
- Extract `key_insight` from observations
- Generate `input_generation` from task analysis
- Extract `puzzle_concepts` from observations/hypotheses

**Option B**: Generate both formats simultaneously
- Keep reasoning trace (for quality assessment)
- Also generate NVARC-compatible description (for pipeline)

**Option C**: Use NVARC code directly
- Adapt our generator to use NVARC's `summary_v1.md` prompt format
- Generate NVARC-style descriptions from the start
- Keep reasoning trace as separate metadata

## Recommendation

**Hybrid approach**: 
1. Keep Trelis trace format (good for reasoning quality)
2. Add converter function: `trace_to_nvarc_description(trace)` 
3. Test converter output through NVARC pipeline
4. This allows both quality assessment AND pipeline integration

