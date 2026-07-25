# 01 — Tech Stack

## Language & Runtime

| Technology | Version | Why |
|---|---|---|
| **Python** | >= 3.11 | Required for `from __future__ import annotations` and modern type-union syntax (`X \| None`) used throughout the codebase. |

## Core Framework

| Dependency | Version | Purpose |
|---|---|---|
| **FastMCP** | >= 2.0 | Provides the `FastMCP` class that creates MCP (Model Context Protocol) servers. Handles tool registration, transport (streamable-http / stdio), and client communication. This is the backbone of the entire server. |
| **Pydantic** | >= 2.0 | Data validation and serialization for VM models ([`VMConfig`](src/vmware_mcp/models.py:21), [`Snapshot`](src/vmware_mcp/models.py:37)). Used with `BaseModel` and `model_validate` / `model_dump` for clean JSON handling. |
| **Requests** | >= 2.28 | HTTP client used by [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) to communicate with the `vmrest.exe` REST API. Supports Basic Auth and session reuse. |
| **python-dotenv** | >= 1.0 | Loads `.env` files at startup in [`config.py`](src/vmware_mcp/config.py:19) so credentials don't need to be hardcoded or passed via shell. |

## Build System

| Tool | Version | Purpose |
|---|---|---|
| **setuptools** | >= 68.0 | Standard Python build backend configured in [`pyproject.toml`](pyproject.toml:21). |
| **uv** | latest | Recommended package manager and virtual environment tool (faster alternative to pip + venv). |

## External Dependency (Runtime)

| Service | Version | Purpose |
|---|---|---|
| **VMware Workstation Pro** | 17+ | The hypervisor whose REST API (`vmrest.exe`) this server wraps. Must be installed and the REST API service must be running on the target Windows host. |
| **vmrest.exe** | bundled with Workstation | HTTP REST API exposing VM management endpoints on port `8697` by default. Requires Windows credentials (Basic Auth). |

## Key Files Referenced

- [`pyproject.toml`](pyproject.toml) — all dependency declarations and entry-point configuration
- [`.env.example`](.env.example) — template for required environment variables
