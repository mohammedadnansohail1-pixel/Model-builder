"""Tests for LoRA trainer."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from app.ml.fine_tuning.lora_trainer import LoRATrainer


class TestLoRATrainer:
    """Test LoRA trainer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_trainer_initialization(self):
        """Test trainer initialization."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
            use_qlora=False,
        )

        assert trainer.model_name == "test/model"
        assert trainer.output_dir == self.temp_dir
        assert trainer.use_qlora is False
        assert trainer.model is None
        assert trainer.tokenizer is None

    def test_trainer_initialization_qlora(self):
        """Test trainer initialization with QLoRA."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
            use_qlora=True,
        )

        assert trainer.use_qlora is True

    @patch("app.ml.fine_tuning.lora_trainer.AutoTokenizer")
    @patch("app.ml.fine_tuning.lora_trainer.AutoModelForCausalLM")
    @patch("app.ml.fine_tuning.lora_trainer.get_peft_model")
    def test_load_model_regular_lora(
        self,
        mock_get_peft_model,
        mock_auto_model,
        mock_tokenizer,
    ):
        """Test loading model with regular LoRA."""
        # Mock tokenizer
        mock_tok = MagicMock()
        mock_tok.pad_token = None
        mock_tok.eos_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = mock_tok

        # Mock model
        mock_model = MagicMock()
        mock_model.print_trainable_parameters = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        mock_get_peft_model.return_value = mock_model

        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
            use_qlora=False,
        )

        lora_config = {
            "lora_r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.1,
        }

        trainer.load_model(lora_config)

        # Verify tokenizer was loaded
        mock_tokenizer.from_pretrained.assert_called_once()
        assert trainer.tokenizer is not None

        # Verify model was loaded without quantization
        mock_auto_model.from_pretrained.assert_called_once()
        call_kwargs = mock_auto_model.from_pretrained.call_args[1]
        assert "quantization_config" not in call_kwargs

        # Verify LoRA was applied
        mock_get_peft_model.assert_called_once()

    @patch("app.ml.fine_tuning.lora_trainer.AutoTokenizer")
    @patch("app.ml.fine_tuning.lora_trainer.AutoModelForCausalLM")
    @patch("app.ml.fine_tuning.lora_trainer.get_peft_model")
    @patch("app.ml.fine_tuning.lora_trainer.prepare_model_for_kbit_training")
    def test_load_model_qlora(
        self,
        mock_prepare_kbit,
        mock_get_peft_model,
        mock_auto_model,
        mock_tokenizer,
    ):
        """Test loading model with QLoRA."""
        # Mock tokenizer
        mock_tok = MagicMock()
        mock_tok.pad_token = "<pad>"
        mock_tokenizer.from_pretrained.return_value = mock_tok

        # Mock model
        mock_model = MagicMock()
        mock_model.print_trainable_parameters = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        mock_prepare_kbit.return_value = mock_model
        mock_get_peft_model.return_value = mock_model

        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
            use_qlora=True,
        )

        lora_config = {
            "lora_r": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
        }

        trainer.load_model(lora_config)

        # Verify model was loaded with quantization
        mock_auto_model.from_pretrained.assert_called_once()
        call_kwargs = mock_auto_model.from_pretrained.call_args[1]
        assert "quantization_config" in call_kwargs

        # Verify k-bit training preparation
        mock_prepare_kbit.assert_called_once()

        # Verify LoRA was applied
        mock_get_peft_model.assert_called_once()

    @patch("app.ml.fine_tuning.lora_trainer.load_dataset")
    def test_prepare_dataset(self, mock_load_dataset):
        """Test dataset preparation."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.column_names = ["text", "label"]
        mock_dataset.map.return_value = mock_dataset
        mock_load_dataset.return_value = mock_dataset

        # Mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": [1, 2, 3]}

        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )
        trainer.tokenizer = mock_tokenizer

        # Create temporary dataset file
        dataset_path = os.path.join(self.temp_dir, "test.json")
        with open(dataset_path, "w") as f:
            f.write('{"text": "hello"}')

        result = trainer.prepare_dataset(
            dataset_path=dataset_path,
            dataset_format="json",
            text_column="text",
            max_length=512,
        )

        # Verify dataset was loaded
        mock_load_dataset.assert_called_once()

        # Verify dataset was tokenized
        mock_dataset.map.assert_called_once()

    def test_prepare_dataset_unsupported_format(self):
        """Test dataset preparation with unsupported format."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )
        trainer.tokenizer = MagicMock()

        with pytest.raises(ValueError, match="Unsupported dataset format"):
            trainer.prepare_dataset(
                dataset_path="test.xyz",
                dataset_format="xyz",
            )

    @patch("app.ml.fine_tuning.lora_trainer.Trainer")
    def test_train(self, mock_trainer_class):
        """Test training."""
        # Mock trainer
        mock_trainer = MagicMock()
        mock_trainer.train.return_value = MagicMock(
            training_loss=0.5,
            metrics={"loss": 0.5}
        )
        mock_trainer_class.return_value = mock_trainer

        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )
        trainer.model = MagicMock()
        trainer.tokenizer = MagicMock()

        # Mock dataset
        mock_dataset = MagicMock()

        result = trainer.train(
            train_dataset=mock_dataset,
            hyperparameters={
                "num_epochs": 3,
                "batch_size": 4,
                "learning_rate": 0.0002,
            },
        )

        # Verify trainer was initialized
        mock_trainer_class.assert_called_once()

        # Verify training was called
        mock_trainer.train.assert_called_once()

        # Verify model was saved
        mock_trainer.save_model.assert_called_once()

        # Verify results
        assert "train_loss" in result
        assert "metrics" in result

    def test_save_model_no_model_loaded(self):
        """Test saving model when no model is loaded."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )

        with pytest.raises(ValueError, match="No model loaded"):
            trainer.save_model(self.temp_dir)

    def test_merge_and_save_no_model_loaded(self):
        """Test merging model when no model is loaded."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )

        with pytest.raises(ValueError, match="No model loaded"):
            trainer.merge_and_save(self.temp_dir)

    def test_merge_and_save(self):
        """Test merging and saving model."""
        trainer = LoRATrainer(
            model_name="test/model",
            output_dir=self.temp_dir,
        )

        # Mock model with merge capability
        mock_merged = MagicMock()
        mock_merged.save_pretrained = Mock()

        mock_model = MagicMock()
        mock_model.merge_and_unload.return_value = mock_merged

        mock_tokenizer = MagicMock()
        mock_tokenizer.save_pretrained = Mock()

        trainer.model = mock_model
        trainer.tokenizer = mock_tokenizer

        output_path = os.path.join(self.temp_dir, "merged")
        trainer.merge_and_save(output_path)

        # Verify merge was called
        mock_model.merge_and_unload.assert_called_once()

        # Verify save was called
        mock_merged.save_pretrained.assert_called_once_with(output_path)
        mock_tokenizer.save_pretrained.assert_called_once_with(output_path)
