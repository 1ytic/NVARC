#!/bin/bash

source /opt/nemo_rl_venv/bin/activate

export PYTHONPATH=/packages/NeMo-RL

export NRL_MEGATRON_CHECKPOINT_DIR=./results/megatron

EXP_NAME="qwen3_4b_grids15_sft139"

uv run ./run_sft.py --config ./configs/sft_mg.yaml \
    checkpointing.checkpoint_dir="results/$EXP_NAME" \
    cluster.num_nodes=4 \
    sft.seed=24 \
    sft.val_period=200 \
    checkpointing.save_period=200 \
    sft.max_num_epochs=1 \
    sft.max_num_steps=12716 \
    sft.val_global_batch_size=256 \
    sft.val_micro_batch_size=1 \
    policy.model_name="/models/Qwen3-4B-Thinking-2507-16t" \
    policy.tokenizer.name="/models/Qwen3-4B-Thinking-2507-16t" \
    policy.train_global_batch_size=256 \
    policy.train_micro_batch_size=1 \
    policy.megatron_cfg.tensor_model_parallel_size=8 \
    policy.megatron_cfg.optimizer.clip_grad=0.5 \
    policy.megatron_cfg.optimizer.lr=0.0001 \
    policy.megatron_cfg.optimizer.min_lr=0.0000001 \
    policy.megatron_cfg.scheduler.lr_warmup_init=0.000001 \
    policy.megatron_cfg.scheduler.lr_warmup_iters=200 \
    policy.megatron_cfg.scheduler.lr_decay_iters=12716 \
    policy.sequence_packing.train_mb_tokens=256000 \
    logger.wandb.name="$EXP_NAME"