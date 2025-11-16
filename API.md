# UniversalTune API Reference

Complete API documentation for UniversalTune platform.

---

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.yourdomain.com/api/v1
```

## Authentication

All endpoints (except auth endpoints) require authentication via JWT tokens.

### Request Header

```
Authorization: Bearer <access_token>
```

### Token Response Format

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-16T10:00:00Z"
}
```

#### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Organizations

#### POST /organizations
Create a new organization.

**Request:**
```json
{
  "name": "My Organization",
  "description": "Organization description"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "My Organization",
  "description": "Organization description",
  "created_at": "2024-01-16T10:00:00Z",
  "created_by": "uuid"
}
```

#### GET /organizations
List user's organizations.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 20, max: 100)

**Response (200):**
```json
[
  {
    "id": "uuid",
    "name": "My Organization",
    "description": "Organization description",
    "created_at": "2024-01-16T10:00:00Z"
  }
]
```

#### POST /organizations/{id}/members
Add member to organization.

**Request:**
```json
{
  "user_id": "uuid",
  "role": "member"
}
```

**Roles:** `owner`, `admin`, `member`, `viewer`

---

### Projects

#### POST /projects
Create a new project.

**Request:**
```json
{
  "name": "My Project",
  "description": "Project description",
  "organization_id": "uuid"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "My Project",
  "description": "Project description",
  "organization_id": "uuid",
  "created_at": "2024-01-16T10:00:00Z"
}
```

#### GET /projects
List projects.

**Query Parameters:**
- `organization_id` (uuid): Filter by organization
- `skip` (int): Pagination offset
- `limit` (int): Results per page

---

### Models

#### POST /models/import
Import model from HuggingFace Hub.

**Request:**
```json
{
  "name": "GPT-2 Small",
  "description": "GPT-2 small model",
  "project_id": "uuid",
  "model_family": "gpt",
  "hf_model_id": "gpt2",
  "model_type": "causal_lm",
  "tags": ["gpt", "text-generation"]
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "GPT-2 Small",
  "model_family": "gpt",
  "hf_model_id": "gpt2",
  "status": "importing",
  "created_at": "2024-01-16T10:00:00Z"
}
```

#### POST /models/upload
Upload custom model.

**Request (multipart/form-data):**
- `file`: Model file
- `name`: Model name
- `project_id`: Project UUID
- `model_family`: Model family
- `model_type`: Model type

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Custom Model",
  "status": "uploading",
  "storage_path": "s3://bucket/path"
}
```

#### GET /models
List models.

**Query Parameters:**
- `project_id` (uuid): Filter by project
- `model_family` (str): Filter by family
- `skip`, `limit`: Pagination

---

### Datasets

#### POST /datasets
Upload dataset.

**Request (multipart/form-data):**
- `file`: Dataset file (CSV, JSON, Parquet)
- `name`: Dataset name
- `project_id`: Project UUID
- `description`: Optional description

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Training Dataset",
  "format": "csv",
  "size_bytes": 1048576,
  "num_rows": 10000,
  "status": "uploading"
}
```

#### GET /datasets/{id}/stats
Get dataset statistics.

**Response (200):**
```json
{
  "num_rows": 10000,
  "num_columns": 5,
  "size_bytes": 1048576,
  "column_stats": {
    "text": {
      "type": "string",
      "null_count": 0,
      "unique_count": 9850
    }
  }
}
```

---

### Training

#### POST /training
Create training job.

**Request:**
```json
{
  "name": "Fine-tune GPT-2",
  "description": "Fine-tuning for customer support",
  "project_id": "uuid",
  "base_model_id": "uuid",
  "dataset_id": "uuid",
  "fine_tuning_method": "lora",
  "hyperparameters": {
    "learning_rate": 2e-4,
    "num_epochs": 3,
    "batch_size": 4,
    "lora_r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.1
  }
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Fine-tune GPT-2",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2024-01-16T10:00:00Z"
}
```

#### GET /training/{id}
Get training job details.

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Fine-tune GPT-2",
  "status": "training",
  "progress": 45.5,
  "current_epoch": 2,
  "total_epochs": 3,
  "current_step": 450,
  "total_steps": 1000,
  "metrics": {
    "loss": 0.45,
    "learning_rate": 0.0002,
    "epoch_time_seconds": 120
  },
  "started_at": "2024-01-16T10:05:00Z"
}
```

**Status values:** `pending`, `training`, `completed`, `failed`, `cancelled`

#### POST /training/{id}/cancel
Cancel training job.

**Response (200):**
```json
{
  "id": "uuid",
  "status": "cancelling"
}
```

---

### Deployments

#### POST /deployments
Deploy a model.

**Request:**
```json
{
  "name": "Production Deployment",
  "description": "Customer support chatbot",
  "project_id": "uuid",
  "model_id": "uuid",
  "backend": "vllm",
  "configuration": {
    "max_batch_size": 32,
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512
  },
  "resource_allocation": {
    "cpu_cores": 4,
    "memory_gb": 16,
    "gpu_count": 1,
    "gpu_type": "nvidia-t4"
  },
  "replicas": 2,
  "auto_scaling_enabled": true
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Production Deployment",
  "status": "deploying",
  "backend": "vllm",
  "created_at": "2024-01-16T10:00:00Z"
}
```

#### POST /deployments/{id}/start
Start a stopped deployment.

**Response (200):**
```json
{
  "id": "uuid",
  "status": "starting"
}
```

#### POST /deployments/{id}/stop
Stop a running deployment.

**Response (200):**
```json
{
  "id": "uuid",
  "status": "stopping"
}
```

#### POST /deployments/{id}/inference
Run inference on deployed model.

**Request:**
```json
{
  "inputs": "What is machine learning?",
  "parameters": {
    "max_tokens": 100,
    "temperature": 0.7
  }
}
```

**Response (200):**
```json
{
  "outputs": "Machine learning is a subset of artificial intelligence...",
  "latency_ms": 145.2,
  "tokens_generated": 42
}
```

#### GET /deployments/{id}/metrics
Get deployment metrics.

**Response (200):**
```json
{
  "total_requests": 10523,
  "total_errors": 12,
  "average_latency_ms": 156.3,
  "requests_per_second": 12.5,
  "gpu_utilization_percent": 78.5,
  "memory_usage_percent": 65.2
}
```

---

### Analytics

#### GET /analytics/dashboard
Get dashboard statistics.

**Response (200):**
```json
{
  "total_users": 150,
  "total_organizations": 45,
  "total_projects": 120,
  "total_models": 230,
  "total_datasets": 180,
  "total_training_jobs": 450,
  "total_deployments": 85,
  "active_deployments": 42,
  "total_api_requests": 1250000,
  "total_errors": 1250
}
```

#### GET /analytics/usage
Get usage summary for billing.

**Query Parameters:**
- `start_time` (datetime): Period start
- `end_time` (datetime): Period end
- `organization_id` (uuid): Filter by organization

**Response (200):**
```json
{
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z",
  "total_gpu_hours": 245.5,
  "total_cpu_hours": 1523.2,
  "total_storage_gb": 450.0,
  "total_api_requests": 125000,
  "total_tokens_generated": 15000000,
  "total_cost": 1250.75,
  "currency": "USD",
  "breakdown_by_resource": {
    "training": {
      "quantity": 125.5,
      "cost": 625.50
    },
    "deployment": {
      "quantity": 120.0,
      "cost": 600.25
    }
  }
}
```

#### GET /analytics/performance
Get performance metrics.

**Query Parameters:**
- `start_time`, `end_time`: Time range

**Response (200):**
```json
{
  "period_start": "2024-01-16T00:00:00Z",
  "period_end": "2024-01-16T23:59:59Z",
  "avg_training_duration_minutes": 45.2,
  "avg_deployment_latency_ms": 156.3,
  "avg_inference_latency_ms": 145.8,
  "success_rate_percentage": 99.5,
  "p50_latency_ms": 125.0,
  "p95_latency_ms": 250.0,
  "p99_latency_ms": 450.0
}
```

#### POST /analytics/events
Track an analytics event.

**Request:**
```json
{
  "event_type": "training_started",
  "event_name": "Fine-tuning Job Started",
  "properties": {
    "model_family": "gpt",
    "dataset_size": 10000
  }
}
```

#### GET /analytics/audit-logs
Get audit logs.

**Query Parameters:**
- `action` (str): Filter by action
- `resource_type` (str): Filter by resource type
- `start_time`, `end_time`: Time range
- `limit`, `offset`: Pagination

**Response (200):**
```json
[
  {
    "id": "uuid",
    "action": "create",
    "resource_type": "model",
    "resource_id": "uuid",
    "user_id": "uuid",
    "changes": {
      "name": "New Model"
    },
    "status": "success",
    "timestamp": "2024-01-16T10:00:00Z"
  }
]
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `500` - Internal Server Error

### Validation Error Example

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

- Default: 60 requests per minute per IP
- Login endpoint: 5 requests per minute per IP
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `skip`: Number of items to skip (default: 0)
- `limit`: Number of items to return (default: 20, max: 100)

**Response includes total count header:**
```
X-Total-Count: 450
```

---

## WebSocket Endpoints

### Training Progress

Connect to receive real-time training updates:

```
ws://localhost:8000/api/v1/training/{id}/ws
```

**Message Format:**
```json
{
  "type": "progress",
  "data": {
    "progress": 55.5,
    "current_epoch": 2,
    "metrics": {
      "loss": 0.35
    }
  }
}
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Create training job
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/training", headers=headers, json={
    "name": "My Training Job",
    "project_id": "uuid",
    "base_model_id": "uuid",
    "dataset_id": "uuid",
    "fine_tuning_method": "lora"
})
print(response.json())
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password"
  })
});
const { access_token } = await loginResponse.json();

// Create training job
const response = await fetch(`${BASE_URL}/training`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${access_token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    name: "My Training Job",
    project_id: "uuid",
    base_model_id: "uuid",
    dataset_id: "uuid",
    fine_tuning_method: "lora"
  })
});
console.log(await response.json());
```

---

## Interactive Documentation

Access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
