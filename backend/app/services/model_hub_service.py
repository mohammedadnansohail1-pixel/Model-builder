"""Model Hub service for HuggingFace integration."""

from typing import List, Optional, Dict, Any
import requests
from app.core.config import settings
from app.schemas.model_registry import HuggingFaceModelInfo


class ModelHubService:
    """Service for interacting with model hubs (primarily HuggingFace)."""

    def __init__(self):
        """Initialize the service."""
        self.hf_api_url = "https://huggingface.co/api"
        self.headers = {}
        if settings.HUGGINGFACE_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.HUGGINGFACE_TOKEN}"

    def search_huggingface_models(
        self,
        query: str,
        model_type: Optional[str] = None,
        limit: int = 20
    ) -> List[HuggingFaceModelInfo]:
        """
        Search for models on HuggingFace.

        Args:
            query: Search query
            model_type: Filter by model type
            limit: Maximum number of results

        Returns:
            List[HuggingFaceModelInfo]: List of model information
        """
        try:
            params = {
                "search": query,
                "limit": limit,
                "sort": "downloads",
                "direction": -1
            }

            if model_type:
                params["filter"] = f"task:{model_type}"

            response = requests.get(
                f"{self.hf_api_url}/models",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            models = []
            for model_data in response.json():
                models.append(HuggingFaceModelInfo(
                    model_id=model_data.get("modelId", model_data.get("id", "")),
                    author=model_data.get("author"),
                    description=model_data.get("lastModified"),  # HF doesn't have description in list
                    downloads=model_data.get("downloads", 0),
                    likes=model_data.get("likes", 0),
                    tags=model_data.get("tags", []),
                    pipeline_tag=model_data.get("pipeline_tag"),
                    model_type=model_data.get("library_name")
                ))

            return models

        except requests.RequestException as e:
            raise Exception(f"Failed to search HuggingFace models: {e}")

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            Dict: Model information
        """
        try:
            response = requests.get(
                f"{self.hf_api_url}/models/{model_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return {
                "model_id": model_id,
                "author": data.get("author"),
                "description": data.get("lastModified"),
                "downloads": data.get("downloads", 0),
                "likes": data.get("likes", 0),
                "tags": data.get("tags", []),
                "pipeline_tag": data.get("pipeline_tag"),
                "model_type": data.get("library_name"),
                "config": data.get("config", {}),
                "siblings": data.get("siblings", [])
            }

        except requests.RequestException as e:
            raise Exception(f"Failed to get model info: {e}")

    def validate_model_exists(self, model_id: str) -> bool:
        """
        Check if a model exists on HuggingFace.

        Args:
            model_id: HuggingFace model ID

        Returns:
            bool: True if model exists
        """
        try:
            response = requests.head(
                f"{self.hf_api_url}/models/{model_id}",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_model_requirements(self, model_id: str) -> Dict[str, Any]:
        """
        Estimate hardware requirements for a model.

        Args:
            model_id: Model identifier

        Returns:
            Dict: Estimated requirements
        """
        try:
            info = self.get_model_info(model_id)

            # Default requirements
            requirements = {
                "min_gpu_memory_gb": 8,
                "min_ram_gb": 16,
                "cuda_version": "11.8",
                "recommended_gpu": "T4"
            }

            # Try to estimate based on model size
            tags = info.get("tags", [])

            # Check for model size indicators
            if "7b" in model_id.lower() or "7b" in str(tags).lower():
                requirements["min_gpu_memory_gb"] = 16
                requirements["recommended_gpu"] = "A10"
            elif "13b" in model_id.lower() or "13b" in str(tags).lower():
                requirements["min_gpu_memory_gb"] = 24
                requirements["recommended_gpu"] = "A100"
            elif "70b" in model_id.lower() or "70b" in str(tags).lower():
                requirements["min_gpu_memory_gb"] = 80
                requirements["recommended_gpu"] = "A100-80GB"

            return requirements

        except Exception:
            # Return default requirements if estimation fails
            return {
                "min_gpu_memory_gb": 8,
                "min_ram_gb": 16,
                "cuda_version": "11.8",
                "recommended_gpu": "T4"
            }


# Global instance
model_hub_service = ModelHubService()
