# NVARC solution to ARC-AGI-2 2025

The full description presented in the paper [here](arc_2025.pdf).

The scripts and prompts for Synthetic Data Generation pipeline could be found in [SDG](SDG) folder.

We also share datasets on Kaggle.

[NVARC Synthetic Puzzles](https://www.kaggle.com/datasets/sorokin/nvarc-synthetic-puzzles) dataset includes our 103k synthetic puzzles.

```bash
kaggle datasets download -d sorokin/nvarc-synthetic-puzzles
unzip nvarc-synthetic-puzzles.zip
```

[NVARC Augmented Puzzles](https://www.kaggle.com/datasets/sorokin/nvarc-augmented-puzzles) dataset includes few subsets with 3.2M augmented puzzles.

```bash
kaggle datasets download -d sorokin/nvarc-augmented-puzzles
unzip nvarc-augmented-puzzles.zip
```

The hyperparameters and fine-tuning scripts for ARChitects model placed in [ARChitects](ARChitects) folder.