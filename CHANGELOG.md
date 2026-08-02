# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-02

### Added
- **Modular Engine Architecture**: Modularized rule definitions under `app/engine/rules/` (`base.py`, `filter.py`, `aggregate.py`, `move.py`, `factory.py`) adhering to Single Responsibility and Open-Closed principles.
- **Polymorphic Rule Validation**: Added `Rule.validate_params` to delegate rule parameter validation to individual rule classes instead of hardcoded `if/elif` statements.
- **Automated Test Suite**: Added 24 comprehensive unit and integration tests covering engine rules, authentication, JWT tokens, background tasks, and FastAPI endpoints.
- **Shared Uploads Volume**: Added shared volume `uploads_data` in `docker-compose.yml` to support multi-container file sharing between API and Celery workers.

### Fixed
- **Celery Worker Retry Logic**: Prevented premature state mutation to `failed` during Celery retry attempts and excluded non-retryable errors (`WorkflowValidationError`, `ValueError`, `FileNotFoundError`) from retrying.
- **Async Event Loop Blocking**: Wrapped synchronous Excel I/O (`pd.read_excel`) in `run_in_threadpool` across FastAPI endpoints (`/files/upload` and `/executions/preview`).
- **Python 3.12+ Deprecations**: Replaced deprecated `datetime.utcnow()` with timezone-aware `datetime.now(timezone.utc)` in maintenance tasks.
- **Pydantic V2 Migration Warnings**: Updated schema configuration classes to `ConfigDict` and `SettingsConfigDict`.
- **Environment Driver Fallbacks**: Added PyJWT/python-jose and SQLite in-memory driver fallbacks for seamless local testing without external database drivers.

### Removed
- **Unused Dependency**: Removed `xlsxwriter` from `requirements.txt` (pandas uses `openpyxl`).

### Security
- Added environment variable validation for `SECRET_KEY` and CORS origin parsing.
