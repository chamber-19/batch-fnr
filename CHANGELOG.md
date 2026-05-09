# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Changed

- Breaking architecture update: repository now runs as a stateless FastAPI backend service.
- Added backend HTTP endpoints: `/api/health`, `/api/scan-folder`, `/api/preview`, `/api/execute`.
- Added backend-side test suite and health-check oriented release workflow.
- Marked `frontend/` and `frontend/src-tauri/` as deprecated (reference-only).

### Removed

- Removed stale migration script `remove-autocad-complete.ps1`.
