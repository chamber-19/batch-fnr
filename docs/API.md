# API Reference

## Base

- Local default: `http://127.0.0.1:8000`

## Endpoints

### GET /api/health

Returns backend health metadata.

Response `200`:

```json
{
  "status": "healthy",
  "service": "batch-fnr-backend",
  "version": "1.0.0"
}
```

### POST /api/scan-folder

Recursively returns `.dwg` files under a folder.

Request:

```json
{
  "folder": "C:/projects/substation-a"
}
```

Response `200`:

```json
{
  "files": [
    "C:/projects/substation-a/A101.dwg",
    "C:/projects/substation-a/B200.dwg"
  ]
}
```

Response `400`: folder missing/invalid.

### POST /api/preview

Runs sidecar `preview` and returns all matches + per-file errors.

Request:

```json
{
  "files": ["C:/projects/A101.dwg"],
  "pairs": [
    {
      "find": "OLD",
      "replace": "NEW",
      "case_sensitive": false,
      "use_regex": false
    }
  ]
}
```

Response `200`:

```json
{
  "status": "complete",
  "matches": [],
  "files_scanned": 1,
  "total_matches": 0,
  "errors": []
}
```

Response `400`: empty `files` or `pairs`.
Response `500`: sidecar not found/protocol/runtime failure.

### POST /api/execute

Runs sidecar `execute` and returns aggregate change counts.

Request body matches `/api/preview`.

Response `200`:

```json
{
  "status": "complete",
  "total_changes": 4,
  "files_modified": 2,
  "errors": []
}
```

Response `400`: empty `files` or `pairs`.
Response `500`: sidecar not found/protocol/runtime failure.
