# Trelis-NVARC

Reasoning trace generation and NVARC integration for ARC-AGI-2.

**Latest Update (Jan 2026)**: Completed generation of 100 reasoning traces and NVARC descriptions using Gemini 2.0 Flash (Avg Quality: 0.54). Codebase aligned with Trelis guidelines (`uv`, concise CLI scripts).

## Usage

This project uses `uv` for dependency management.

### Generate Traces
```bash
uv run arc_trace_generator.py --batch 100
```

### Assess Quality
```bash
uv run trace_quality.py traces/
```

### Convert to NVARC
```bash
uv run trace_to_nvarc.py --input-dir traces --output-dir traces
```

Refer to script help (`-h`) for more options.
