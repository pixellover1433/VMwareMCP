# 01 — Tech Stack

## Language & Runtime

| Technology | Version | Why |
|---|---|---|
| **Python** | >= 3.11 | Required for `from __future__ import annotations` and modern type-union syntax (`X \| None`) used throughout the codebase. |

## Core Framework

| Dependency | Version | Purpose |
|---|---|---|
| **FastMCP** | >= 2.0 | Provides the `FastMCP` class that creates MCP (Model Context Protocol) servers. Handles tool registration, transport (streamable-http / stdio), and client communication. This is the backbone of the entire server. |
| **Pydantic** | >= 2.0 | Data validation and serialization for API/CLI models ([`VMConfig`](src/vmware_mcp/models.py:19), [`Snapshot`](src/vmware_mcp/models.py:35), [`SnapshotQueryResult`](src/vmware_mcp/models.py:50)). Used with `BaseModel` and `model_validate` / `model_dump` for clean JSON handling. |
| **Requests** | >= 2.28 | HTTP client used by [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) to communicate with the `vmrest.exe` REST API. Supports Basic Auth and session reuse. |
| **python-dotenv** | >= 1.0 | Loads `.env` files at startup in [`config.py`](src/vmware_mcp/config.py:19) so credentials don't need to be hardcoded or passed via shell. |

## Standard Library (Notable Usage)

| Module | Purpose |
|---|---|
| **subprocess** | Used by [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) to invoke the local `vmcli.exe` binary for operations not exposed by the REST API (e.g., snapshot queries). |
| **pathlib** | Validates the existence of `vmcli.exe` before invocation, and resolves the `.env` path in config. |
| **urllib.parse** | URL-encodes opaque VM IDs before embedding them in REST API paths. |

## Build System

| Tool | Version | Purpose |
|---|---|---|
| **setuptools** | >= 68.0 | Standard Python build backend configured in [`pyproject.toml`](pyproject.toml:16). Uses `src-layout` package discovery. |
| **uv** | latest | Recommended package manager and virtual environment tool (faster alternative to pip + venv). |

## External Dependencies (Runtime)

| Service | Version | Purpose |
|---|---|---|
| **VMware Workstation Pro** | 17+ | The hypervisor this server manages. Must be installed on the target Windows host. |
| **vmrest.exe** | bundled with Workstation | HTTP REST API exposing VM management endpoints on port `8697` by default. Requires Windows credentials (Basic Auth). Used for **listing VMs, power control, config, and network info**. |
| **vmcli.exe** | bundled with Workstation | Local command-line tool at `C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe` (configurable). Used for **snapshot queries** which the REST API does not expose. **Requires the MCP server to run on the same host as VMware Workstation.** |

## Architectural Note: Two Backend Channels

This project talks to VMware Workstation through **two distinct channels**:

1. **`vmrest.exe` (HTTP)** — the primary channel for most operations. Can be local or remote.
2. **`vmcli.exe` (subprocess)** — a local-only fallback for capabilities missing from the REST API (currently snapshot listing). Because it shells out to a local binary, snapshot tools only work when the server is co-located with VMware Workstation.

## Key Files Referenced

- [`pyproject.toml`](pyproject.toml) — all dependency declarations and entry-point configuration
- [`.env.example`](.env.example) — template for required environment variables
