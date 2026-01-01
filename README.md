# Trelis-NVARC

Reasoning trace generation and NVARC integration for ARC-AGI-2.

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
