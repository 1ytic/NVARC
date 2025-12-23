# Trelis Fork Notes

>![IMPORTANT]
> DEVELOPER NOTES: a) Keep in touch with Ronan via WhatsApp re progress, b) Ronan will provide written feedback at least once per month on progress / quality and will add/remove/change repo access based on quality standards/progress c) if you no longer have time to advance research, let Ronan know, d) developers who have contributed will be credited in any X / Youtube posts/videos. See [here](https://github.com/TrelisResearch/style-guide) for a very short style guide.

The idea is to build a seed dataset of ARC AGI II **training** and later **public evaluation** tasks that can be used to create sythnthetic data as in the NVARC pipeline.

## A) Seed trace collection (two options)
We will support two trace sources:

**Option A1 — Human trace (Axel)**
- Axel records himself solving AA2 training tasks on stream (audio/video).
- We transcribe and convert into structured traces.

**Option A2 — LLM trace (Dheeraj)**
- Use **Gemini Flash 3.0** to generate traces for the same AA2 training tasks.

Ultimately this should give us two datasets. Ideally, we have ways to assess the quality of seed task descriptions (and, later, the quality of compounded descriptions).

## B) Synthetic expansion
Once traces/descriptions are solid, we will implement the “compounding descriptions → code” pipeline:
- augment descriptions with metadata,
- compound into harder descriptions,
- generate input-grid generator code,
- generate solver code,
- verify.

Here we are following NVARC.

## Training
We can choose to pre-train a Qwen model OR we can decide to train a VARC type model (which is smaller and likely requires less pre-training).

---

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
