# NVARC solution to ARC-AGI-2 2025

This repository contains the code and instructions to replicate the NVARC submissions to the [Arc Prize 2025 competition on Kaggle](https://www.kaggle.com/competitions/arc-prize-2025).

The NVARC team includes Ivan Sorokin and Jean-Francois Puget, who are also members of the NVIDIA [KGMoN](https://www.nvidia.com/en-us/ai-data-science/kaggle-grandmasters) team.

The solution is described in the [paper](nvarc_2025.pdf) and consists of three main components:

- Multi-stage synthetic data generation pipeline;
- Improved version of the ARChitects solution that won the [ARC Prize competition in 2024](https://www.kaggle.com/competitions/arc-prize-2024);
- Improved version of Tiny Recursive Models by Alexia Jolicoeur-Martineau.

## Synthetic Data Generation

The scripts and prompts for Synthetic Data Generation pipeline can be found in [SDG](SDG) folder.

[NVARC Artifacts Puzzles](https://www.kaggle.com/datasets/sorokin/nvarc-artifacts-puzzles) dataset includes generated text used to construct the synthetic puzzles.

```bash
kaggle datasets download -d sorokin/nvarc-artifacts-puzzles
unzip nvarc-artifacts-puzzles.zip
```

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

Visualization of synthetic puzzles shown in the Kaggle notebook [nvarc-viewer](https://www.kaggle.com/code/sorokin/nvarc-viewer).

## The ARChitects

The hyperparameters and fine-tuning scripts for the Qwen3 4B model are located in the [ARChitects](ARChitects) folder.

The submission notebook is available on Kaggle [sorokin/arc2-qwen3-unsloth-flash-lora-batch4-queue](https://www.kaggle.com/code/sorokin/arc2-qwen3-unsloth-flash-lora-batch4-queue).

## Tiny Recursive Models

The scripts and instructions to train Tiny Recursive Models are in the [TRM](TRM) folder.

The submission notebook is available on Kaggle [cpmpml/arc2-trm-v31](https://www.kaggle.com/code/cpmpml/arc2-trm-v31?scriptVersionId=278223801).

## ARC AGI 2024

We ran our winning solution on last year ARC AGI evaluation data. The code can be found in the [ARC-AGI1](ARC-AGI1) folder.
