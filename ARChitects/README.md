# Supervised Fine-Tuning

1. Assume we have the following subsets with augmented puzzles:
    - arc2_training
    - arc2_evaluation6
    - mini
    - concept
    - rearc
    - nvarc_training
    - nvarc_full
> **_NOTE:_** These augmented puzzles produced by [build_datasets.py](../SDG/scripts/build_datasets.py) script and also available on Kaggle [NVARC Augmented Puzzles](https://www.kaggle.com/datasets/sorokin/nvarc-augmented-puzzles) dataset.
2. Prepare Qwen3 tokenizer and model with 16 embeddings.
3. Execute `run_sft_4b.sh` script on Slurm cluster.