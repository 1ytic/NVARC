# NVARC solution to ARC-AGI-2 2025

This repository contains the code and instructions to replicate NVARC submissions to the [Arc Prize 2025 competition on Kaggle](https://www.kaggle.com/competitions/arc-prize-2025). NVARC team includes Ivan Sorokin and Jean-Francois Puget, both working at NVIDIA at the time of the competition.

The solution full description is presented in the paper [here](nvarc_2025.pdf).

The solution has three main components:
- Multi stage synthetic data generation;
- Improved version of The Architect solution that won the arc prize compeittion in 2024;
- Improved version of Tiny Recursive Models by Alexia Jolicoeur-Martineau.

## Synthetic Data Generation

The scripts and prompts for Synthetic Data Generation pipeline can be found in [SDG](SDG) folder.

We also share generated datasets on Kaggle.

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
## The Architect 
The hyperparameters and fine-tuning scripts for ARChitects model are placed in [ARChitects](ARChitects) folder.

## Tiny Recurive Models
The scripts and instructions to train Tiny Recursive Models are in the [TRM](TRM) folder.
