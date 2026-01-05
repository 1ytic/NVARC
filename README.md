# Trelis-NVARC

ARC-AGI-2 NVARC description generation and synthetic dataset creation using Gemini 3 Flash.

## Overview

This project implements the NVARC SDG (Synthetic Data Generation) pipeline for ARC-AGI-2 tasks, using Gemini 3 Flash as the LLM. The pipeline uses only SDG prompts and does not generate intermediate JSON traces.

## NVARC SDG Pipeline

The complete pipeline follows these steps:

1. **Generate descriptions (.nvarc.md)** using `SDG/prompts/summary_v2.md` with Gemini 3 Flash
2. **[SKIPPED]** Task mixing using `mix_v2.md` - we skip this step
3. **Generate input code** using `SDG/prompts/generate_puzzle_input.md` prompt with Gemini 3 Flash
4. **Generate output code** using `SDG/prompts/generate_puzzle_output.md` prompt with Gemini 3 Flash
5. **Execute input logic** to generate input grids
6. **Execute output logic** to generate output grids
7. **Make pairs** from input/output grids
8. **Build final dataset** with augmentations

**Simplified Approach**: This pipeline directly generates `.nvarc.md` files using SDG prompts, without intermediate JSON traces.

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run complete pipeline on 3 sample tasks
python3 run_nvarc_pipeline.py

# Run on specific tasks
python3 run_nvarc_pipeline.py --task-ids 007bbfb7,00d62c1b

# Run on 10 random tasks
python3 run_nvarc_pipeline.py --all-tasks --count 10

# Generate more grids per task
python3 run_nvarc_pipeline.py --task-ids 007bbfb7 --num-grids 50

# Skip certain steps (e.g., regenerate grids only)
python3 run_nvarc_pipeline.py --skip descriptions,code_generation
```

## Pipeline Outputs

After running the pipeline, you'll find:

- `traces/` - Puzzle descriptions (.nvarc.md files in XML format)
- `logic/` - Generated Python code for input/output generation
- `synthetic/grids_arc_input/` - Generated input grids
- `synthetic/grids_arc_output/` - Generated output grids
- `synthetic/pairs_arc/` - Input/output grid pairs
- `synthetic/arc_dataset.json` - Final dataset with augmentations

## Individual Scripts

You can also run individual steps:

```bash
# Step 1: Generate descriptions (.nvarc.md) from ARC tasks using SDG summary_v2.md
python3 generate_summaries.py --task 007bbfb7
python3 generate_summaries.py --batch 100

# Steps 3-4: Generate input/output code from descriptions
python3 seed_to_logic.py --batch 10

# Step 5: Generate input grids from code
python3 SDG/scripts/generate_input_grids.py \
  --inputs-mask "logic/*.py" \
  --grids-prefix "synthetic/grids_arc_input" \
  --num-grids 30

# Step 6: Generate output grids
python3 SDG/scripts/generate_output_grids.py \
  --solutions-mask "logic/*.py" \
  --input-grids-prefix "synthetic/grids_arc_input" \
  --output-grids-prefix "synthetic/grids_arc_output"

# Step 7: Create pairs
python3 SDG/scripts/make_pairs.py \
  --input-grids-prefix "synthetic/grids_arc_input" \
  --output-grids-mask "synthetic/grids_arc_output/*/*.json" \
  --output-prefix "synthetic/pairs_arc"

# Step 8: Build dataset
python3 SDG/scripts/build_datasets.py \
  --input-prefix "synthetic/pairs_arc" \
  --output-dataset "synthetic/arc_dataset.json" \
  --augmentations dihedral color
```

## Testing

Test generated code on original ARC tasks:

```bash
python3 test_on_original_tasks.py --batch --output test_results.json
```

## Key Differences from Original NVARC

- **Task mixing skipped**: We don't use the `mix_v2.md` prompt to create mixed puzzles
- **Gemini 3 Flash**: Uses `gemini-3-flash-preview` model instead of GPT/other LLMs
- **Clean room compliance**: Uses only ARC-AGI-2 training challenges, no test/evaluation data

