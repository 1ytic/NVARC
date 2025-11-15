# Training Tiny Recurive Models (TRM) for ARC AGI2

This directory contains the code and data we used to pretrain the TRM we used during the arc prize 2025 competition.

This code has been tested on Kaggle container image 2025-10-06, on a machine with 8 H100 GPUs. It depends on the TRM code cloned in the `../external/` directory. Installing TRM in another container image may require a different installation procedure. Please refer to https://github.com/SamsungSAILMontreal/TinyRecursiveModels/ for general installation.

The following bash commands must be run in this directory.

## 1. Install TRM.

```bash
pip install hydra-core==1.3.2 adam_atan2_pytorch==0.2.4 argdantic==1.3.3 coolname==2.2.0 numba==0.62.1

ln -s ../external/TinyRecursiveModels/models .
ln -s ../external/TinyRecursiveModels/puzzle_dataset.py .
ln -s ../external/TinyRecursiveModels/dataset .
ln -s ../external/TinyRecursiveModels/utils .
ln -s ../external/TinyRecursiveModels/evaluators .
ln -s ../external/TinyRecursiveModels/assets .
ln -s ../external/TinyRecursiveModels/config .
ln -s ../external/TinyRecursiveModels/kaggle .

```

## 2. Download the TRM training dataset.
Download from `https://www.kaggle.com/datasets/cpmpml/arc-prize-trm-training-data` into the `arc-prize-trm-training-data` directory, then unzip the archive. This dataset contains 4073 puzzles (the competition puzzles plus about 3k datasets from our SDG pipeline). We used 256 augmentations, which produced a total of 1041207 puzzles. 

## 3. Download the TRM evaluation dataset.
Download from `https://www.kaggle.com/datasets/cpmpml/arc-prize-trm-evaluation-data` into the `arc-prize-trm-evaluation-data` directory, then unzip the archive. This dataset was created with 128 augmentations per puzzle, to match what we use in Kaggle notebooks.

## 4. Pretrain the model. 

We removed the wandb dependency as well as the model evaluation during training in order to speed up training. It is possible to use the `pretrain.py` script in the TinyRecursiveModels repository if you prefer to use wandb and evaluation during training. In that case make sure to adapt the traing command.

```bash
torchrun --standalone --nnodes=1 --nproc-per-node 8 --rdzv_backend=c10d --rdzv_endpoint=localhost:0 \
pretrain-no-eval.py \
arch=trm \
data_paths="[arc-prize-trm-training-data]" \
arch.L_layers=2 \
arch.H_cycles=3 arch.L_cycles=4 \
ema=True \
evaluators=[] \
lr=0.0003 \
+checkpoint_path=./checkpoint \
global_batch_size=3072 \
eval_interval=1000 \
epochs=10000
```

This will save 10 checkpoints in the `checkpoint` directory. We uploaded these to a [kaggle dataset](https://www.kaggle.com/datasets/cpmpml/arc-prize-trm-031) and used them in our submissions.

## 5. Evaluate the model (Optional).

We can also evaluate this model on the competition evaluation data with the following command. We use 4 GPUs only, and we limit batch size, to mimick what we can run on Kaggle notebooks. Note that we also changed some TRM hyper parameters because they yield better results during the test time fine tuning step.

```bash
torchrun --standalone --nnodes=1 --nproc-per-node 4 --rdzv_backend=c10d --rdzv_endpoint=localhost:0 \
eval-arc-k-10.py \
arch=trm \
data_paths="[arc-prize-trm-evaluation-data]" \
arch.L_layers=2 \
arch.H_cycles=4 arch.L_cycles=4 arch.halt_max_steps=10 \
+load_checkpoint=./checkpoint/step_220708  \
eval_interval=2000 \
epochs=2000 \
global_batch_size=128 \
ema=True \
+checkpoint_path=./checkpoint-eval \
lr_warmup_steps=200 \
lr=0.0001
```

This evaluation produced these statistics when we ran it:

```bash
{'all': {'accuracy': 0.7744678, 'exact_accuracy': 0.043603994, 'lm_loss': 1.2915632, 'q_halt_accuracy': 0.76508063, 'q_halt_loss': 0.6607322, 'steps': 10.0}, 'ARC/pass@1': 0.0763888888888889, 'ARC/pass@2': 0.1013888888888889, 'ARC/pass@5': 0.1013888888888889, 'ARC/pass@10': 0.1013888888888889, 'ARC/pass@100': 0.1375, 'ARC/pass@1000': 0.1375}
```
When submitted this scored 10.0 on Kaggle public leaderboard, version 18 of this notebook `https://www.kaggle.com/code/cpmpml/arc2-trm-v31?scriptVersionId=278223801`
