# API Documentation

## Overview

The Macro Builder API provides a RESTful interface for creating and executing Excel automation workflows.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: Bearer JWT token

## Authentication Flow

### 1. Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "company_name": "My Company"
}
```

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### 2. Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## Workflows

### Create Workflow
```http
POST /workflows
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Monthly Report",
  "description": "Process monthly sales data"
}
```

### List Workflows
```http
GET /workflows
Authorization: Bearer {token}
```

### Create Workflow Version
```http
POST /workflows/{workflow_id}/versions
Authorization: Bearer {token}
Content-Type: application/json

{
  "rules": {
    "steps": [
      {
        "type": "filter",
        "column": "Status",
        "operator": "=",
        "value": "Active"
      }
    ]
  }
}
```

## Rule Types

### Filter Rule
Filters rows based on a condition.

```json
{
  "type": "filter",
  "column": "ColumnName",
  "operator": "=",
  "value": "TargetValue"
}
```

**Operators**: `=`, `!=`, `>`, `<`, `>=`, `<=`, `contains`

### Move Rule
Moves current dataframe to a named output sheet.

```json
{
  "type": "move",
  "target_sheet": "SheetName"
}
```

### GroupSum Rule
Groups by one column and sums another.

```json
{
  "type": "group_sum",
  "group_by": "Category",
  "field": "Amount",
  "target_sheet": "Summary"
}
```

## Files

### Upload File
```http
POST /files/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file=@path/to/file.xlsx
```

**Response**:
```json
{
  "file_id": "uuid",
  "filename": "file.xlsx",
  "columns": ["Col1", "Col2", "Col3"]
}
```

### Download File
```http
GET /files/{file_id}/download
Authorization: Bearer {token}
```

## Executions

### Start Execution
```http
POST /executions
Authorization: Bearer {token}
Content-Type: application/json

{
  "workflow_version_id": "uuid",
  "file_id": "uuid"
}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "pending",
  "workflow_version_id": "uuid",
  "started_at": null,
  "finished_at": null,
  "error_message": null
}
```

### Get Execution Status
```http
GET /executions/{execution_id}
Authorization: Bearer {token}
```

**Statuses**: `pending`, `running`, `success`, `failed`

### Get Execution Logs
```http
GET /executions/{execution_id}/logs
Authorization: Bearer {token}
```

**Response**:
```json
[
  {
    "step_index": 0,
    "step_type": "filter",
    "message": "Filtered by Status = Active",
    "affected_rows": 150,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### Download Output
```http
GET /executions/{execution_id}/output
Authorization: Bearer {token}
```

Returns Excel file.

### Preview Workflow
```http
POST /executions/preview
Authorization: Bearer {token}
Content-Type: application/json

{
  "file_id": "uuid",
  "rules": {
    "steps": [...]
  }
}
```

**Response**:
```json
{
  "before": [...],
  "after": {
    "sheet": "Output",
    "rows": [...]
  },
  "logs": [...]
}
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

**Error Response Format**:
```json
{
  "detail": "Error message description"
}
```

## Rate Limiting

Currently no rate limiting is enforced. In production, implement per-user rate limits.

## Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI with interactive API testing.
