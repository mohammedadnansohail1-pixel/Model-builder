"""Tests for training API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.training import TrainingJob, TrainingStatus, FineTuningMethod
from app.models.user import User
from app.models.project import Project
from app.models.model_registry import ModelRegistry
from app.models.dataset import Dataset


@pytest.mark.asyncio
class TestTrainingAPI:
    """Test training API endpoints."""

    async def test_create_training_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test creating a training job."""
        data = {
            "name": "Test Training Job",
            "description": "Test description",
            "project_id": str(test_project.id),
            "base_model_id": str(test_model.id),
            "dataset_id": str(test_dataset.id),
            "fine_tuning_method": "lora",
            "hyperparameters": {
                "num_epochs": 3,
                "batch_size": 4,
                "learning_rate": 0.0002,
                "lora_r": 16,
                "lora_alpha": 32,
            },
        }

        response = await client.post(
            "/api/v1/training",
            json=data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Test Training Job"
        assert result["status"] == "queued"
        assert result["fine_tuning_method"] == "lora"
        assert "id" in result

    async def test_create_training_job_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test creating training job without authentication."""
        data = {
            "name": "Test Job",
            "project_id": str(test_project.id),
            "base_model_id": str(test_model.id),
            "dataset_id": str(test_dataset.id),
            "fine_tuning_method": "lora",
        }

        response = await client.post("/api/v1/training", json=data)
        assert response.status_code == 401

    async def test_list_training_jobs(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test listing training jobs."""
        # Create some test jobs
        job1 = TrainingJob(
            id=uuid.uuid4(),
            name="Job 1",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.LORA,
            hyperparameters={"num_epochs": 3},
            status=TrainingStatus.QUEUED,
            total_epochs=3,
            metrics={},
            compute_used={},
            created_by=test_user.id,
        )
        job2 = TrainingJob(
            id=uuid.uuid4(),
            name="Job 2",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.QLORA,
            hyperparameters={"num_epochs": 5},
            status=TrainingStatus.COMPLETED,
            total_epochs=5,
            metrics={},
            compute_used={},
            created_by=test_user.id,
        )
        db_session.add_all([job1, job2])
        await db_session.commit()

        # Test listing all jobs
        response = await client.get("/api/v1/training", headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 2

        # Test filtering by status
        response = await client.get(
            "/api/v1/training",
            params={"status": "completed"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert all(job["status"] == "completed" for job in result)

        # Test filtering by project
        response = await client.get(
            "/api/v1/training",
            params={"project_id": str(test_project.id)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 2

    async def test_get_training_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test getting a single training job."""
        job = TrainingJob(
            id=uuid.uuid4(),
            name="Test Job",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.LORA,
            hyperparameters={"num_epochs": 3},
            status=TrainingStatus.RUNNING,
            progress=50.0,
            total_epochs=3,
            current_epoch=2,
            metrics={"train_loss": [0.5, 0.3]},
            latest_train_loss=0.3,
            compute_used={},
            created_by=test_user.id,
        )
        db_session.add(job)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/training/{job.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(job.id)
        assert result["name"] == "Test Job"
        assert result["status"] == "running"
        assert result["progress"] == 50.0
        assert result["latest_train_loss"] == 0.3

    async def test_get_training_job_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent training job."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/training/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_training_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test updating a training job."""
        job = TrainingJob(
            id=uuid.uuid4(),
            name="Old Name",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.LORA,
            hyperparameters={"num_epochs": 3},
            status=TrainingStatus.QUEUED,
            total_epochs=3,
            metrics={},
            compute_used={},
            created_by=test_user.id,
        )
        db_session.add(job)
        await db_session.commit()

        update_data = {
            "name": "New Name",
            "description": "Updated description",
        }

        response = await client.put(
            f"/api/v1/training/{job.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "New Name"
        assert result["description"] == "Updated description"

    async def test_cancel_training_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test cancelling a training job."""
        job = TrainingJob(
            id=uuid.uuid4(),
            name="Running Job",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.LORA,
            hyperparameters={"num_epochs": 3},
            status=TrainingStatus.RUNNING,
            total_epochs=3,
            metrics={},
            compute_used={},
            created_by=test_user.id,
        )
        db_session.add(job)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/training/{job.id}/cancel",
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "cancelled"

    async def test_delete_training_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user: User,
        test_project: Project,
        test_model: ModelRegistry,
        test_dataset: Dataset,
    ):
        """Test deleting a training job."""
        job = TrainingJob(
            id=uuid.uuid4(),
            name="Job to Delete",
            project_id=test_project.id,
            base_model_id=test_model.id,
            dataset_id=test_dataset.id,
            fine_tuning_method=FineTuningMethod.LORA,
            hyperparameters={"num_epochs": 3},
            status=TrainingStatus.COMPLETED,
            total_epochs=3,
            metrics={},
            compute_used={},
            created_by=test_user.id,
        )
        db_session.add(job)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/training/{job.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify job is deleted
        response = await client.get(
            f"/api/v1/training/{job.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_list_training_configs(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing training configurations."""
        response = await client.get(
            "/api/v1/training/configs",
            headers=auth_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
