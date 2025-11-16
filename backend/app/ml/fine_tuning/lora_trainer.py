"""LoRA fine-tuning trainer."""

import os
import torch
from typing import Dict, Any, Optional, Callable
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import load_dataset
import logging

logger = logging.getLogger(__name__)


class LoRATrainer:
    """LoRA fine-tuning trainer."""

    def __init__(
        self,
        model_name: str,
        output_dir: str,
        use_qlora: bool = False,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize LoRA trainer.

        Args:
            model_name: HuggingFace model name or path
            output_dir: Directory to save outputs
            use_qlora: Whether to use QLoRA (4-bit quantization)
            device: Device to use for training
        """
        self.model_name = model_name
        self.output_dir = output_dir
        self.use_qlora = use_qlora
        self.device = device
        self.model = None
        self.tokenizer = None
        self.trainer = None

    def load_model(
        self,
        lora_config: Dict[str, Any]
    ) -> None:
        """
        Load model with LoRA configuration.

        Args:
            lora_config: LoRA configuration parameters
        """
        logger.info(f"Loading model: {self.model_name}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Add pad token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with appropriate settings
        if self.use_qlora:
            # QLoRA: 4-bit quantization
            from transformers import BitsAndBytesConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )

            # Prepare for k-bit training
            self.model = prepare_model_for_kbit_training(self.model)
        else:
            # Regular LoRA
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

        # Configure LoRA
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_config.get("lora_r", 16),
            lora_alpha=lora_config.get("lora_alpha", 32),
            lora_dropout=lora_config.get("lora_dropout", 0.1),
            target_modules=lora_config.get("target_modules", ["q_proj", "v_proj"]),
            bias="none"
        )

        # Apply LoRA
        self.model = get_peft_model(self.model, peft_config)
        self.model.print_trainable_parameters()

        logger.info("Model loaded successfully with LoRA")

    def prepare_dataset(
        self,
        dataset_path: str,
        dataset_format: str = "json",
        text_column: str = "text",
        max_length: int = 512
    ) -> Any:
        """
        Prepare dataset for training.

        Args:
            dataset_path: Path to dataset file
            dataset_format: Format of dataset (json, csv, etc.)
            text_column: Column containing text data
            max_length: Maximum sequence length

        Returns:
            Prepared dataset
        """
        logger.info(f"Loading dataset from: {dataset_path}")

        # Load dataset
        if dataset_format == "json":
            dataset = load_dataset("json", data_files=dataset_path, split="train")
        elif dataset_format == "jsonl":
            dataset = load_dataset("json", data_files=dataset_path, split="train")
        elif dataset_format == "csv":
            dataset = load_dataset("csv", data_files=dataset_path, split="train")
        else:
            raise ValueError(f"Unsupported dataset format: {dataset_format}")

        # Tokenize function
        def tokenize_function(examples):
            return self.tokenizer(
                examples[text_column],
                truncation=True,
                max_length=max_length,
                padding="max_length"
            )

        # Tokenize dataset
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )

        logger.info(f"Dataset prepared: {len(tokenized_dataset)} examples")
        return tokenized_dataset

    def train(
        self,
        train_dataset: Any,
        eval_dataset: Optional[Any] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Train the model.

        Args:
            train_dataset: Training dataset
            eval_dataset: Evaluation dataset (optional)
            hyperparameters: Training hyperparameters
            progress_callback: Callback for progress updates

        Returns:
            Training metrics
        """
        logger.info("Starting training...")

        # Default hyperparameters
        hp = hyperparameters or {}

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=hp.get("num_epochs", 3),
            per_device_train_batch_size=hp.get("batch_size", 4),
            gradient_accumulation_steps=hp.get("gradient_accumulation_steps", 1),
            learning_rate=hp.get("learning_rate", 2e-4),
            warmup_steps=hp.get("warmup_steps", 100),
            weight_decay=hp.get("weight_decay", 0.01),
            logging_dir=f"{self.output_dir}/logs",
            logging_steps=10,
            save_strategy="epoch",
            evaluation_strategy="epoch" if eval_dataset else "no",
            save_total_limit=3,
            load_best_model_at_end=True if eval_dataset else False,
            report_to="none",  # Disable wandb, tensorboard, etc.
            fp16=not self.use_qlora,  # Use fp16 for regular LoRA
            bf16=self.use_qlora,  # Use bf16 for QLoRA
            max_grad_norm=hp.get("max_grad_norm", 1.0),
            optim="paged_adamw_32bit" if self.use_qlora else "adamw_torch"
        )

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )

        # Custom callback for progress
        from transformers import TrainerCallback

        class ProgressCallback(TrainerCallback):
            def __init__(self, callback_fn):
                self.callback_fn = callback_fn

            def on_log(self, args, state, control, logs=None, **kwargs):
                if self.callback_fn and logs:
                    self.callback_fn(state, logs)

        callbacks = []
        if progress_callback:
            callbacks.append(ProgressCallback(progress_callback))

        # Initialize trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            callbacks=callbacks
        )

        # Train
        train_result = self.trainer.train()

        # Save final model
        self.trainer.save_model(self.output_dir)

        logger.info("Training completed!")

        return {
            "train_loss": train_result.training_loss,
            "metrics": train_result.metrics
        }

    def save_model(self, path: str) -> None:
        """
        Save the trained model.

        Args:
            path: Path to save model
        """
        if self.model is None:
            raise ValueError("No model loaded")

        logger.info(f"Saving model to: {path}")
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    def merge_and_save(self, output_path: str) -> None:
        """
        Merge LoRA weights with base model and save.

        Args:
            output_path: Path to save merged model
        """
        if self.model is None:
            raise ValueError("No model loaded")

        logger.info("Merging LoRA weights with base model...")

        # Merge and unload
        merged_model = self.model.merge_and_unload()

        # Save merged model
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        logger.info(f"Merged model saved to: {output_path}")
