ge# 02 — Architecture

## High-Level Design

VMwareMCP is an **MCP (Model Context Protocol) server** that bridges AI assistants to VMware Workstation's `vmrest.exe` REST API. The architecture follows a **layered module pattern**:

```
AI Assistant (MCP Client)
        │  streamable-http / stdio
        ▼
┌─────────────────────────────┐
│  FastMCP Server             │  ← server.py (entry point)
│  ┌─────────┐ ┌───────────┐ │
│  │ VM Tools│ │Power Tools│ │  ← modules/*.py (domain logic)
│  └────┬────┘ └─────┬─────┘ │
│       └──────┬─────┘        │
│              ▼              │
│     VMRestClient            │  ← vmrest_client.py (HTTP layer)
│     (requests.Session)      │
└──────────────┬──────────────┘
               │  HTTP Basic Auth
               ▼
        vmrest.exe REST API    ← VMware Workstation (port 8697)
```

## Folder Structure

```
VMwareMCP/
├── src/vmware_mcp/               # Main Python package
│   ├── __init__.py               # Package marker + version string
│   ├── server.py                 # FastMCP instance creation, module registration, entry point
│   ├── config.py                 # Environment variable loading → VMRestHostConfig dataclass
│   ├── models.py                 # Pydantic models (VMConfig, Snapshot, VMCPU)
│   ├── vmrest_client.py          # HTTP client wrapping all vmrest.exe API calls
│   └── modules/                  # Domain-specific MCP tool modules
│       ├── __init__.py           # Module docstring
│       ├── vm.py                 # VM listing and detail tools
│       ├── power.py              # Power state query and control tools
│       └── snapshot.py           # Placeholder (tools removed)
├── pyproject.toml                # Project metadata, dependencies, entry point
├── .env.example                  # Environment variable template
├── README.md                     # User-facing documentation
├── .gitignore                    # Ignored files
├── .vscode/                      # VS Code debug configuration
└── .roo/                         # Custom rules and commands
```

## Component Responsibilities

### [`config.py`](src/vmware_mcp/config.py) — Configuration Layer
- Loads `.env` file from project root using `python-dotenv`.
- Reads `VMREST_HOST`, `VMREST_PORT`, `VMREST_USERNAME`, `VMREST_PASSWORD`, `VMREST_VERIFY_SSL` from environment.
- Returns a [`VMRestHostConfig`](src/vmware_mcp/config.py:23) dataclass with a [`base_url`](src/vmware_mcp/config.py:33) property.
- Raises `RuntimeError` if `VMREST_HOST` is not set.

### [`vmrest_client.py`](src/vmware_mcp/vmrest_client.py) — HTTP Client Layer
- [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) wraps all `vmrest.exe` REST calls using `requests.Session` with Basic Auth.
- Provides typed methods: [`get_vms()`](src/vmware_mcp/vmrest_client.py:87), [`get_vm()`](src/vmware_mcp/vmrest_client.py:123), [`get_power_state()`](src/vmware_mcp/vmrest_client.py:112), [`power_operation()`](src/vmware_mcp/vmrest_client.py:151), [`get_snapshots()`](src/vmware_mcp/vmrest_client.py:179), [`create_snapshot()`](src/vmware_mcp/vmrest_client.py:198), [`delete_snapshot()`](src/vmware_mcp/vmrest_client.py:219), [`revert_snapshot()`](src/vmware_mcp/vmrest_client.py:225).
- Raises [`VMRestClientError`](src/vmware_mcp/vmrest_client.py:17) with HTTP status code on failures.
- URL-encodes VM IDs (opaque unique identifiers returned by `list_vms`) using `urllib.parse.quote`.

### [`models.py`](src/vmware_mcp/models.py) — Data Models
- [`VMCPU`](src/vmware_mcp/models.py:15) — processor count.
- [`VMConfig`](src/vmware_mcp/models.py:21) — id, cpu, memory (from `/api/vms/{id}/restrictions`).
- [`Snapshot`](src/vmware_mcp/models.py:37) — id, name, description, created, parent_id.

### [`server.py`](src/vmware_mcp/server.py) — Entry Point
- Creates the [`FastMCP`](src/vmware_mcp/server.py:30) instance with server name and instructions.
- [`get_client()`](src/vmware_mcp/server.py:51) lazily initializes the global [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25).
- [`_register_modules()`](src/vmware_mcp/server.py:67) imports tool modules, calls their `register(client)`, and mounts their `tools` FastMCP instances onto the main server.
- [`main()`](src/vmware_mcp/server.py:86) runs the server on streamable-http transport port 51001.

### `modules/*.py` — Tool Modules
Each module follows the same pattern:
1. Creates its own `FastMCP` instance (`tools`).
2. Exposes a `register(client)` function that sets the module-level client and defines `@tools.tool()` decorated functions.
3. Tools return JSON strings (never raw objects) for clean MCP responses.
4. Errors are caught and returned as structured JSON error objects, never raised to the client.

#### [`modules/vm.py`](src/vmware_mcp/modules/vm.py)
- [`list_vms()`](src/vmware_mcp/modules/vm.py:30) — Lists all VMs with id, path, name, power_state, and ip.
- [`get_vm_details(vm_id)`](src/vmware_mcp/modules/vm.py:82) — Returns detailed config, power state, and network info for a VM.
- Helper: [`_extract_primary_ip()`](src/vmware_mcp/modules/vm.py:129), [`_extract_network_info()`](src/vmware_mcp/modules/vm.py:144).

#### [`modules/power.py`](src/vmware_mcp/modules/power.py)
- [`get_vm_power_state(vm_id)`](src/vmware_mcp/modules/power.py:29) — Returns current power state.
- [`set_vm_power_state(vm_id, operation)`](src/vmware_mcp/modules/power.py:56) — Performs power operations (on, off, suspend, shutdown, restart, pause, unpause, reset).

#### [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py)
- Placeholder module — snapshot MCP tools have been removed. The module is retained for future use.

## Data Flow

1. **Client → Server**: An MCP client sends a tool call (e.g., `list_vms`) over streamable-http to port 51001.
2. **Server → Module**: FastMCP routes the call to the registered tool function in the appropriate module.
3. **Module → Client**: The tool function uses the shared [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) to make HTTP requests to `vmrest.exe`.
4. **Client → vmrest**: [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) sends authenticated HTTP requests to `http://{host}:8697/api/vms/...`.
5. **Module → Response**: The tool function formats the response as a JSON string and returns it through FastMCP back to the MCP client.

## Design Patterns

- **Module Pattern**: Domain tools are isolated in separate modules with a consistent `register(client)` + `tools` interface, enabling easy addition of new tool categories.
- **Lazy Singleton**: The [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) is created once on first access via [`get_client()`](src/vmware_mcp/server.py:51) and shared across all modules.
- **Dataclass for Config, Pydantic for API Models**: Configuration uses `@dataclass` for simplicity; API response models use Pydantic `BaseModel` for validation and serialization.
- **Error-as-Return**: Tools catch exceptions and return structured JSON error objects rather than propagating exceptions to the MCP client.
