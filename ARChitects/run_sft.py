import argparse
import pprint
from typing import Any

from omegaconf import OmegaConf

from nemo_rl.algorithms.sft import MasterConfig, setup, sft_train
from nemo_rl.algorithms.utils import get_tokenizer
from nemo_rl.data.datasets import AllTaskProcessedDataset
from nemo_rl.data.interfaces import DatumSpec, TaskDataSpec
from nemo_rl.data.llm_message_utils import get_formatted_message_log
from nemo_rl.distributed.virtual_cluster import init_ray
from nemo_rl.utils.config import load_config, parse_hydra_overrides
from nemo_rl.utils.logger import get_next_experiment_dir

from datasets import load_from_disk, concatenate_datasets


PRINTED_SAMPLE = False

def sft_preprocessor(
    sample: dict[str, Any],
    task_data_spec: TaskDataSpec,
    tokenizer,
    max_seq_length: int,
    idx: int,
) -> DatumSpec:
    global PRINTED_SAMPLE

    tokenized_messages = get_formatted_message_log(
        sample["messages"],
        tokenizer,
        task_data_spec,
        add_bos_token=False,
        add_eos_token=False,
        add_generation_prompt=True,
    )

    length = sum(len(m["token_ids"]) for m in tokenized_messages)

    if not PRINTED_SAMPLE:
        PRINTED_SAMPLE = True
        print(f"\n\nExample sample {idx} with {len(tokenized_messages)} messages and {length} length:")
        for m in tokenized_messages:
            num_tokens = len(m["token_ids"])
            print(f"\nrole: {m['role']}, tokens: {num_tokens}")
            print(f"content start: {m['content'][:100]!r} ...")
            print(f"content end: ... {m['content'][-100:]!r}")
            print(f"token ids start: {m['token_ids'][:100]} ...")
            print(f"token ids end: ... {m['token_ids'][-100:]}")
        print("\n\n")

    return {
        "message_log": tokenized_messages,
        "length": length,
        "extra_env_info": None,
        "loss_multiplier": 1.0,
        "idx": idx,
    }


def load_datasets(path):
    if isinstance(path, str):
        ds = load_from_disk(path)
    else:
        dss = []
        for name in path:
            ds = load_from_disk(name)
            print(f"Dataset {name}:\n{ds}")
            dss.append(ds)
        ds = concatenate_datasets(dss)
    return ds


def main():

    parser = argparse.ArgumentParser(description="Run SFT training with configuration")
    parser.add_argument("--config", type=str, help="Path to YAML config file")

    args, overrides = parser.parse_known_args()

    config = load_config(args.config)
    print(f"Loaded configuration from: {args.config}")

    if overrides:
        print(f"Overrides: {overrides}")
        config = parse_hydra_overrides(config, overrides)

    config: MasterConfig = OmegaConf.to_container(config, resolve=True)
    print("Applied CLI overrides")

    print("Final config:")
    pprint.pprint(config)

    config["logger"]["log_dir"] = get_next_experiment_dir(config["logger"]["log_dir"])
    print(f"📊 Using log directory: {config['logger']['log_dir']}")

    if config["checkpointing"]["enabled"]:
        print(f"📊 Using checkpoint directory: {config['checkpointing']['checkpoint_dir']}")

    init_ray()

    tokenizer = get_tokenizer(config["policy"]["tokenizer"])
    print(f"Tokenizer size: {len(tokenizer)}")

    print("\n▶ Setting up data...")

    sft_task_spec = TaskDataSpec(task_name="AGI")

    train_dataset = load_datasets(config["data"]["train_dataset_path"])
    train_dataset = train_dataset.shuffle(seed=config["sft"]["seed"])
    print(f"Loaded training samples:\n{train_dataset}")

    val_dataset = load_datasets(config["data"]["val_dataset_path"])
    print(f"Loaded validation samples:\n{val_dataset}")

    train_dataset = AllTaskProcessedDataset(
        train_dataset,
        tokenizer,
        sft_task_spec,
        sft_preprocessor,
    )

    val_dataset = AllTaskProcessedDataset(
        val_dataset,
        tokenizer,
        sft_task_spec,
        sft_preprocessor,
    )

    (
        policy,
        cluster,
        train_dataloader,
        val_dataloader,
        loss_fn,
        logger,
        checkpointer,
        sft_save_state,
        master_config,
    ) = setup(config, tokenizer, train_dataset, val_dataset)

    sft_train(
        policy,
        train_dataloader,
        val_dataloader,
        tokenizer,
        loss_fn,
        master_config,
        logger,
        sft_task_spec,
        checkpointer,
        sft_save_state,
    )


if __name__ == "__main__":
    main()
