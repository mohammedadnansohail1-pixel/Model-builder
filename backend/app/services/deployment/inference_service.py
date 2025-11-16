"""Inference service for running model predictions."""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.deployment import Deployment, InferenceLog, DeploymentStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class InferenceService:
    """Service for running model inference."""

    def __init__(self, db: AsyncSession):
        """
        Initialize inference service.

        Args:
            db: Database session
        """
        self.db = db

    async def run_inference(
        self,
        deployment_id: uuid.UUID,
        inputs: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None,
        api_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run inference on a deployment.

        Args:
            deployment_id: Deployment ID
            inputs: Input text
            parameters: Generation parameters
            user_id: User making request
            api_key: API key used
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Inference result

        Raises:
            ValueError: If deployment not found or not running
        """
        # Get deployment
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        deployment = result.scalar_one_or_none()

        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.status != DeploymentStatus.RUNNING:
            raise ValueError(
                f"Deployment is {deployment.status}, must be running"
            )

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Merge parameters with deployment defaults
        params = {**deployment.configuration, **(parameters or {})}

        # Start timing
        start_time = time.time()

        try:
            # TODO: Call actual inference backend (TGI, vLLM, etc.)
            # For now, simulate inference
            generated_text = await self._simulate_inference(inputs, params)

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            tokens_input = len(inputs.split())  # Simplified token count
            tokens_output = len(generated_text.split())
            tokens_per_second = tokens_output / (latency_ms / 1000) if latency_ms > 0 else 0

            # Create response
            response_data = {
                "generated_text": generated_text,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "latency_ms": latency_ms,
                "tokens_per_second": tokens_per_second,
                "finish_reason": "length",
            }

            # Log inference
            await self._log_inference(
                deployment=deployment,
                request_id=request_id,
                request_data={"inputs": inputs, "parameters": params},
                response_data=response_data,
                latency_ms=latency_ms,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_per_second=tokens_per_second,
                status_code=200,
                success=True,
                user_id=user_id,
                api_key=api_key,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Update deployment metrics
            await self._update_deployment_metrics(
                deployment=deployment,
                latency_ms=latency_ms,
                success=True,
            )

            return response_data

        except Exception as e:
            # Calculate latency even for errors
            latency_ms = (time.time() - start_time) * 1000

            logger.error(f"Inference error for deployment {deployment_id}: {str(e)}")

            # Log failed inference
            await self._log_inference(
                deployment=deployment,
                request_id=request_id,
                request_data={"inputs": inputs, "parameters": params},
                response_data=None,
                latency_ms=latency_ms,
                status_code=500,
                success=False,
                error_message=str(e),
                user_id=user_id,
                api_key=api_key,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Update deployment metrics
            await self._update_deployment_metrics(
                deployment=deployment,
                latency_ms=latency_ms,
                success=False,
            )

            raise

    async def get_inference_logs(
        self,
        deployment_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
        success_only: Optional[bool] = None,
    ) -> list[InferenceLog]:
        """
        Get inference logs for a deployment.

        Args:
            deployment_id: Deployment ID
            limit: Maximum number of logs
            offset: Offset for pagination
            success_only: Filter by success status

        Returns:
            List of inference logs
        """
        query = select(InferenceLog).where(
            InferenceLog.deployment_id == deployment_id
        )

        if success_only is not None:
            query = query.where(InferenceLog.success == success_only)

        query = query.order_by(InferenceLog.timestamp.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _simulate_inference(
        self, inputs: str, parameters: Dict[str, Any]
    ) -> str:
        """
        Simulate inference for demo purposes.

        Args:
            inputs: Input text
            parameters: Generation parameters

        Returns:
            Generated text
        """
        # TODO: Replace with actual inference backend call
        # This is just a simulation
        max_tokens = parameters.get("max_new_tokens", 100)

        # Simulate processing time
        await self.db.execute(select(1))  # Dummy query for async context

        # Generate dummy response
        return f"Generated response for: {inputs[:50]}... (simulated with {max_tokens} max tokens)"

    async def _log_inference(
        self,
        deployment: Deployment,
        request_id: str,
        request_data: Dict[str, Any],
        latency_ms: float,
        status_code: int,
        success: bool,
        response_data: Optional[Dict[str, Any]] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        tokens_per_second: Optional[float] = None,
        error_message: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        api_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log inference request.

        Args:
            deployment: Deployment
            request_id: Request ID
            request_data: Request data
            latency_ms: Request latency
            status_code: HTTP status code
            success: Whether request succeeded
            response_data: Response data
            tokens_input: Input token count
            tokens_output: Output token count
            tokens_per_second: Generation speed
            error_message: Error message if failed
            user_id: User making request
            api_key: API key used
            ip_address: Client IP
            user_agent: Client user agent
        """
        log = InferenceLog(
            id=uuid.uuid4(),
            deployment_id=deployment.id,
            request_id=request_id,
            endpoint_path="/generate",
            method="POST",
            request_data=request_data,
            response_data=response_data,
            latency_ms=latency_ms,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_per_second=tokens_per_second,
            status_code=status_code,
            error_message=error_message,
            success=success,
            user_id=user_id,
            api_key_used=api_key,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(log)
        await self.db.commit()

    async def _update_deployment_metrics(
        self,
        deployment: Deployment,
        latency_ms: float,
        success: bool,
    ) -> None:
        """
        Update deployment metrics.

        Args:
            deployment: Deployment
            latency_ms: Request latency
            success: Whether request succeeded
        """
        # Update counters
        deployment.total_requests += 1
        if not success:
            deployment.total_errors += 1

        # Update average latency (running average)
        if deployment.average_latency_ms is None:
            deployment.average_latency_ms = latency_ms
        else:
            # Exponential moving average
            alpha = 0.1
            deployment.average_latency_ms = (
                alpha * latency_ms + (1 - alpha) * deployment.average_latency_ms
            )

        # Calculate requests per minute (last 100 requests)
        # TODO: Calculate from actual time window
        deployment.requests_per_minute = min(deployment.total_requests, 100.0)

        await self.db.commit()
