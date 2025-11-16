"""Training tasks for Celery."""

import os
import logging
from datetime import datetime
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.models.training import TrainingJob, TrainingStatus
from app.models.model_registry import ModelRegistry
from app.models.dataset import Dataset
from app.ml.fine_tuning.lora_trainer import LoRATrainer
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

# Create sync database engine for Celery tasks
sync_engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, name="train_model")
def train_model(self, job_id: str):
    """
    Celery task to train a model.

    Args:
        job_id: Training job ID

    Returns:
        dict: Training results
    """
    db = SessionLocal()

    try:
        # Get training job
        job = db.query(TrainingJob).filter(TrainingJob.id == UUID(job_id)).first()
        if not job:
            raise ValueError(f"Training job {job_id} not found")

        logger.info(f"Starting training job: {job.name} ({job_id})")

        # Update status
        job.status = TrainingStatus.INITIALIZING
        job.started_at = datetime.utcnow()
        db.commit()

        # Get model and dataset
        model = db.query(ModelRegistry).filter(ModelRegistry.id == job.base_model_id).first()
        dataset = db.query(Dataset).filter(Dataset.id == job.dataset_id).first()

        if not model or not dataset:
            raise ValueError("Model or dataset not found")

        # Download dataset from storage
        dataset_local_path = f"/tmp/datasets/{job_id}"
        os.makedirs(dataset_local_path, exist_ok=True)
        dataset_file = f"{dataset_local_path}/{dataset.original_filename}"

        logger.info(f"Downloading dataset: {dataset.file_path}")
        dataset_content = storage_service.download_file(dataset.file_path)
        with open(dataset_file, "wb") as f:
            f.write(dataset_content)

        # Set up output directory
        output_dir = f"/tmp/training/{job_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Initialize trainer
        use_qlora = job.fine_tuning_method.value == "qlora"
        trainer = LoRATrainer(
            model_name=model.model_id,
            output_dir=output_dir,
            use_qlora=use_qlora
        )

        # Update status
        job.status = TrainingStatus.RUNNING
        db.commit()

        # Load model with LoRA config
        lora_config = {
            "lora_r": job.hyperparameters.get("lora_r", 16),
            "lora_alpha": job.hyperparameters.get("lora_alpha", 32),
            "lora_dropout": job.hyperparameters.get("lora_dropout", 0.1),
            "target_modules": job.hyperparameters.get("target_modules", ["q_proj", "v_proj"])
        }
        trainer.load_model(lora_config)

        # Prepare dataset
        train_dataset = trainer.prepare_dataset(
            dataset_path=dataset_file,
            dataset_format=dataset.format.value,
            max_length=job.hyperparameters.get("max_length", 512)
        )

        # Progress callback
        def progress_callback(state, logs):
            """Update job progress in database."""
            try:
                job.current_epoch = state.epoch if hasattr(state, 'epoch') else 0
                job.current_step = state.global_step if hasattr(state, 'global_step') else 0
                job.total_steps = state.max_steps if hasattr(state, 'max_steps') else None

                # Update metrics
                if "loss" in logs:
                    job.latest_train_loss = logs["loss"]
                    if not job.metrics.get("train_loss"):
                        job.metrics["train_loss"] = []
                    job.metrics["train_loss"].append({
                        "step": state.global_step,
                        "value": logs["loss"]
                    })

                if "eval_loss" in logs:
                    job.latest_eval_loss = logs["eval_loss"]
                    if not job.best_eval_loss or logs["eval_loss"] < job.best_eval_loss:
                        job.best_eval_loss = logs["eval_loss"]

                # Calculate progress
                if state.max_steps:
                    job.progress = (state.global_step / state.max_steps) * 100

                # Add to logs
                log_message = f"Step {state.global_step}: {logs}\n"
                job.logs += log_message

                db.commit()
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

        # Train
        result = trainer.train(
            train_dataset=train_dataset,
            hyperparameters=job.hyperparameters,
            progress_callback=progress_callback
        )

        # Save trained model to storage
        model_output_path = f"models/trained/{job_id}"
        trainer.save_model(output_dir)

        # Upload to MinIO
        logger.info("Uploading trained model to storage...")
        # TODO: Upload model files to MinIO

        # Update job
        job.status = TrainingStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 100.0
        job.output_model_path = model_output_path
        job.logs += f"\n\nTraining completed successfully!\nFinal loss: {result.get('train_loss')}\n"

        db.commit()

        logger.info(f"Training job {job_id} completed successfully")

        return {
            "job_id": job_id,
            "status": "completed",
            "train_loss": result.get("train_loss"),
            "output_path": model_output_path
        }

    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}")

        # Update job status
        try:
            job = db.query(TrainingJob).filter(TrainingJob.id == UUID(job_id)).first()
            if job:
                job.status = TrainingStatus.FAILED
                job.error_message = str(e)
                job.logs += f"\n\nError: {str(e)}\n"
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")

        raise

    finally:
        db.close()


@celery_app.task(name="cancel_training")
def cancel_training(job_id: str):
    """
    Cancel a training job.

    Args:
        job_id: Training job ID
    """
    db = SessionLocal()

    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == UUID(job_id)).first()
        if job:
            job.status = TrainingStatus.CANCELLED
            job.logs += "\n\nTraining cancelled by user.\n"
            db.commit()

            logger.info(f"Training job {job_id} cancelled")

    finally:
        db.close()
