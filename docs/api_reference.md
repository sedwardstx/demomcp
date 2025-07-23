# MCP Log Analyzer API Reference

## Overview

The MCP (Model Context Protocol) Log Analyzer provides a REST API for analyzing different types of logs on Windows systems. This document describes the available endpoints and their usage.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:5000/api
```

## Authentication

Authentication is not implemented in the current version. In a production environment, you would want to add proper authentication mechanisms.

## Common Response Format

All API responses follow a common format:

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "status": "success|error",
  "error": "error-message-if-status-is-error",
  ... endpoint-specific fields ...
}
```

## Endpoints

### Health Check

```
GET /health
```

Check if the server is running.

**Response:**

```json
{
  "status": "ok"
}
```

### Register Log Source

```
POST /sources
```

Register a new log source for analysis.

**Request:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "client_id": "optional-client-id",
  "name": "log-source-name",
  "type": "event|structured|csv|unstructured",
  "path": "path-to-log-source",
  "metadata": {
    "optional-key1": "optional-value1",
    "optional-key2": "optional-value2"
  }
}
```

**Response:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "status": "success",
  "source": {
    "id": "uuid-string",
    "name": "log-source-name",
    "type": "event|structured|csv|unstructured",
    "path": "path-to-log-source",
    "created_at": "iso-datetime-string",
    "updated_at": "iso-datetime-string",
    "metadata": {
      "key1": "value1",
      "key2": "value2"
    }
  }
}
```

### List Log Sources

```
GET /sources
```

List all registered log sources.

**Response:**

```json
[
  {
    "id": "uuid-string",
    "name": "log-source-name",
    "type": "event|structured|csv|unstructured",
    "path": "path-to-log-source",
    "created_at": "iso-datetime-string",
    "updated_at": "iso-datetime-string",
    "metadata": {
      "key1": "value1",
      "key2": "value2"
    }
  },
  ...
]
```

### Get Log Source

```
GET /sources/{source_id}
```

Get details of a specific log source.

**Response:**

```json
{
  "id": "uuid-string",
  "name": "log-source-name",
  "type": "event|structured|csv|unstructured",
  "path": "path-to-log-source",
  "created_at": "iso-datetime-string",
  "updated_at": "iso-datetime-string",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

### Delete Log Source

```
DELETE /sources/{source_id}
```

Delete a registered log source.

**Response:**

```json
{
  "status": "success",
  "message": "Log source {source_id} deleted"
}
```

### Query Logs

```
POST /query
```

Query logs from registered sources.

**Request:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "client_id": "optional-client-id",
  "query": {
    "source_ids": ["optional-uuid-string1", "optional-uuid-string2"],
    "types": ["optional-log-type1", "optional-log-type2"],
    "start_time": "optional-iso-datetime-string",
    "end_time": "optional-iso-datetime-string",
    "filters": {
      "optional-field1": "optional-value1",
      "optional-field2": "optional-value2"
    },
    "limit": 100,
    "offset": 0
  }
}
```

**Response:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "status": "success",
  "records": [
    {
      "id": "uuid-string",
      "source_id": "uuid-string",
      "timestamp": "iso-datetime-string",
      "data": {
        "field1": "value1",
        "field2": "value2",
        ...
      },
      "raw_data": "optional-raw-data-string"
    },
    ...
  ],
  "total": 1234,
  "limit": 100,
  "offset": 0
}
```

### Analyze Logs

```
POST /analyze
```

Analyze logs from registered sources.

**Request:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "client_id": "optional-client-id",
  "query": {
    "source_ids": ["optional-uuid-string1", "optional-uuid-string2"],
    "types": ["optional-log-type1", "optional-log-type2"],
    "start_time": "optional-iso-datetime-string",
    "end_time": "optional-iso-datetime-string",
    "filters": {
      "optional-field1": "optional-value1",
      "optional-field2": "optional-value2"
    },
    "limit": 100,
    "offset": 0
  },
  "analysis_type": "analysis-type",
  "parameters": {
    "optional-param1": "optional-value1",
    "optional-param2": "optional-value2"
  }
}
```

**Response:**

```json
{
  "request_id": "uuid-string",
  "timestamp": "iso-datetime-string",
  "status": "success",
  "results": {
    "analysis_type": "analysis-type",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    },
    "summary": "summary-string",
    "details": {
      ... analysis-specific-details ...
    }
  },
  "query": {
    ... query-object-from-request ...
  }
}
```

## Error Handling

If an error occurs, the response will have a status of "error" and an error message:

```json
{
  "status": "error",
  "error": "Error message"
}
```

HTTP status codes are also used to indicate errors:
- 400: Bad Request - The request was invalid
- 404: Not Found - The requested resource was not found
- 500: Internal Server Error - An unexpected error occurred on the server

## Log Types

The following log types are supported:

- `event`: Windows Event Logs (EVT/EVTX)
- `structured`: Structured Logs (JSON, XML)
- `csv`: CSV Logs
- `unstructured`: Unstructured Text Logs 