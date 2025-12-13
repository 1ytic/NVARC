Code to run our Qwen 4B model on ARC-AGI 2024 evaluation data.

The code is the same as in the notebook we used for our winning solution in Kaggle: [sorokin/arc2-qwen3-unsloth-flash-lora-batch4-queue](https://www.kaggle.com/code/sorokin/arc2-qwen3-unsloth-flash-lora-batch4-queue).

The variant in this folder moved all the installation scripts into the `pip-install-unsloth-flash-patch.ipynb` notebook. It should be run in Kaggle docker image available in December 2025.

The evaluation code is in the notebook: `002_ivan_arc1.ipynb` Theonly modifications compared to the kaggle notebook is to do test time fine tuning with the public evaluation data from arc prize 2024.


