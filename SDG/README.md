# Synthetic Puzzles

1. Prepare H-ARC user comments [scripts/h_arc_clean.py](scripts/h_arc_clean.py)
2. Prepare BARC descriptions [scripts/barc_clean.py](scripts/barc_clean.py)
3. Generate puzzle summaries with prompt [prompts/summary_v1.md](prompts/summary_v1.md)
4. Generate mix summaries with prompt [prompts/mix_v1.md](prompts/mix_v1.md)
5. Generate input logic with prompt [prompts/generate_puzzle_input.md](prompts/generate_puzzle_input.md)
6. Generate output logic with prompt [prompts/generate_puzzle_output.md](prompts/generate_puzzle_output.md)
7. Execute input logic and make input grids [scripts/generate_input_grids.py](scripts/generate_input_grids.py)
8. Execute output logic and make output grids [scripts/generate_output_grids.py](scripts/generate_output_grids.py)
9. Join and filter input/output grids into pairs [scripts/make_pairs.py](scripts/make_pairs.py)
10. Create dataset with augmented puzzles [scripts/build_datasets.py](scripts/build_datasets.py)


> **NOTE:** We recommend using the [NeMo-Skills](https://github.com/NVIDIA-NeMo/Skills) framework to generate data with LLMs. You can find more instructions on how to use this framework [here](https://nvidia-nemo.github.io/Skills/tutorials/2025/08/29/inference-with-gpt-oss-120b-using-stateful-python-code-execution/#synthetic-data-generation).
