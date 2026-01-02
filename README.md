# Trelis-NVARC

ARC-AGI-2 NVARC description generation using Gemini 3 Flash.

## Usage

```bash
# Generate NVARC descriptions from ARC tasks
python3 generate_descriptions.py -h

# Test generated code on original tasks
python3 test_on_original_tasks.py -h

# Run full pipeline
python3 run_nvarc_pipeline.py -h
```

## Workflow

1. Generate descriptions: `python3 generate_descriptions.py --batch 100`
2. Generate code (use `verify_trace_quality.py` or NeMo-Skills)
3. Test quality: `python3 test_on_original_tasks.py --batch`

