# 02 — Architecture

## High-Level Design

VMwareMCP is an **MCP (Model Context Protocol) server** that bridges AI assistants to VMware Workstation. It uses a **layered module pattern** and talks to the hypervisor through **two backend channels**: the `vmrest.exe` HTTP REST API (primary) and the local `vmcli.exe` binary (fallback for snapshot queries).

```
AI Assistant (MCP Client)
        │  streamable-http / stdio
        ▼
┌───────────────────────────────────────────────┐
│  FastMCP Server                 ← server.py     │
│  ┌──────┐ ┌───────┐ ┌────────┐ ┌────────────┐ │
│  │  VM  │ │ Power │ │ Health │ │ Snapshot   │ │ ← modules/*.py
│  └──┬───┘ └───┬───┘ └───┬────┘ └──┬──────┬──┘ │
│     └─────────┴─────────┘         │      │     │
│              ▼                     ▼      ▼     │
│        VMRestClient  ◄────────────┘  VMCliClient│ ← client layer
│      (requests.Session)              (subprocess)│
└──────────────┬───────────────────────────┬──────┘
               │ HTTP Basic Auth            │ local process exec
               ▼                            ▼
        vmrest.exe REST API           vmcli.exe
        (port 8697, local/remote)     (local host only)
               │                            │
               └────────────┬───────────────┘
                            ▼
                  VMware Workstation Pro
```

**Key insight:** The Snapshot module depends on **both** clients. It uses `VMRestClient` to resolve a VM `id` → `.vmx` path, then uses `VMCliClient` to query snapshots via the local binary.

## Folder Structure

```
VMwareMCP/
├── src/vmware_mcp/               # Main Python package (src-layout)
│   ├── __init__.py               # Package marker + version string
│   ├── server.py                 # FastMCP instance, client accessors, module registration, entry point
│   ├── config.py                 # Env var loading → VMRestHostConfig dataclass (incl. vmcli_path)
│   ├── models.py                 # Pydantic models (VMCPU, VMConfig, Snapshot, SnapshotQueryResult)
│   ├── vmrest_client.py          # HTTP client wrapping vmrest.exe REST API calls
│   ├── vmcli_client.py           # Subprocess client wrapping the local vmcli.exe binary
│   └── modules/                  # Domain-specific MCP tool modules
│       ├── __init__.py           # Module docstring
│       ├── vm.py                 # VM listing and detail tools
│       ├── power.py              # Power state query and control tools
│       ├── health.py             # Server/backend health check tool
│       └── snapshot.py           # Snapshot listing tool (via vmcli)
├── project-knowledge/            # This documentation (source of truth)
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
- Reads `VMREST_HOST`, `VMREST_PORT`, `VMREST_USERNAME`, `VMREST_PASSWORD`, `VMREST_VERIFY_SSL`, and `VMCLI_PATH` from environment.
- Returns a [`VMRestHostConfig`](src/vmware_mcp/config.py:26) dataclass with a [`base_url`](src/vmware_mcp/config.py:37) property and a [`vmcli_path`](src/vmware_mcp/config.py:35) field (defaults to the standard Workstation install path).
- Raises `RuntimeError` if `VMREST_HOST` is not set.

### [`vmrest_client.py`](src/vmware_mcp/vmrest_client.py) — HTTP Client Layer
- [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) wraps `vmrest.exe` REST calls using `requests.Session` with Basic Auth.
- Provides typed methods: [`health_check()`](src/vmware_mcp/vmrest_client.py:77), [`get_vms()`](src/vmware_mcp/vmrest_client.py:135), [`get_vm_path()`](src/vmware_mcp/vmrest_client.py:160), [`get_power_state()`](src/vmware_mcp/vmrest_client.py:182), [`get_vm()`](src/vmware_mcp/vmrest_client.py:193), [`get_vm_nic_ips()`](src/vmware_mcp/vmrest_client.py:205), [`power_operation()`](src/vmware_mcp/vmrest_client.py:221), and the (unused-by-tools) snapshot REST methods [`get_snapshots()`](src/vmware_mcp/vmrest_client.py:263), [`create_snapshot()`](src/vmware_mcp/vmrest_client.py:282), [`delete_snapshot()`](src/vmware_mcp/vmrest_client.py:303), [`revert_snapshot()`](src/vmware_mcp/vmrest_client.py:309).
- Raises [`VMRestClientError`](src/vmware_mcp/vmrest_client.py:17) (carries HTTP status code) on failures.
- URL-encodes VM IDs (opaque identifiers) using `urllib.parse.quote`.
- **Note on IDs vs paths:** The vmrest `id` and `path` are *distinct* values. `GET /api/vms/{id}` does NOT return the path — so [`get_vm_path()`](src/vmware_mcp/vmrest_client.py:160) queries `GET /api/vms` and matches by `id` to find the `.vmx` path.

### [`vmcli_client.py`](src/vmware_mcp/vmcli_client.py) — Subprocess Client Layer
- [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) wraps the local `vmcli.exe` binary via `subprocess.run`.
- [`get_snapshots(vmx_path)`](src/vmware_mcp/vmcli_client.py:90) runs `vmcli snapshot <vmx_path> query --format json`, parses the raw output (`currentUID`, `snapshots[].uid/parentUID/displayName`), and returns a [`SnapshotQueryResult`](src/vmware_mcp/models.py:50) with `is_current` computed per snapshot.
- Raises [`VMCliError`](src/vmware_mcp/vmcli_client.py:26) on missing binary, non-zero exit, timeout, or unparseable JSON — with actionable messages.
- Enforces a 60-second timeout and validates the binary exists before running.

### [`models.py`](src/vmware_mcp/models.py) — Data Models
- [`VMCPU`](src/vmware_mcp/models.py:13) — processor count.
- [`VMConfig`](src/vmware_mcp/models.py:19) — id, cpu, memory (from `/api/vms/{id}/restrictions`).
- [`Snapshot`](src/vmware_mcp/models.py:35) — uid, name, parent_uid, is_current (from `vmcli` output).
- [`SnapshotQueryResult`](src/vmware_mcp/models.py:50) — vmx_path, current_uid, count, snapshots list.

### [`server.py`](src/vmware_mcp/server.py) — Entry Point
- Creates the [`FastMCP`](src/vmware_mcp/server.py:31) instance with server name and instructions.
- [`get_client()`](src/vmware_mcp/server.py:55) lazily initializes the global [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25).
- [`get_vmcli()`](src/vmware_mcp/server.py:67) lazily initializes the global [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) (sharing the same config).
- [`_register_modules()`](src/vmware_mcp/server.py:82) imports tool modules, calls their `register(...)`, and mounts their `tools` FastMCP instances onto the main server.
- [`main()`](src/vmware_mcp/server.py:110) runs the server on streamable-http transport port 51001.

### `modules/*.py` — Tool Modules
Each module follows the same pattern:
1. Creates its own `FastMCP` instance (`tools`) with descriptive `instructions`.
2. Exposes a `register(...)` function that sets module-level client(s) and defines `@tools.tool()` decorated functions.
3. Tools return JSON strings (never raw objects) for clean MCP responses.
4. Errors are caught and returned as structured JSON error objects, never raised to the client.

#### [`modules/vm.py`](src/vmware_mcp/modules/vm.py)
- [`list_vms()`](src/vmware_mcp/modules/vm.py:30) — Lists all VMs with id, path, name, power_state, and ip.
- [`get_vm_details(vm_id)`](src/vmware_mcp/modules/vm.py:82) — Returns detailed config, power state, and network info.

#### [`modules/power.py`](src/vmware_mcp/modules/power.py)
- [`get_vm_power_state(vm_id)`](src/vmware_mcp/modules/power.py:29) — Returns current power state.
- [`set_vm_power_state(vm_id, operation)`](src/vmware_mcp/modules/power.py:56) — Power operations (on, off, suspend, shutdown, pause, unpause).

#### [`modules/health.py`](src/vmware_mcp/modules/health.py)
- [`check_server_health()`](src/vmware_mcp/modules/health.py:30) — Verifies the server can reach and authenticate against the vmrest backend. Returns `status` (healthy/unhealthy), `reachable`, `base_url`, `vm_count`, and error details. Uses `VMRestClient` only.

#### [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py)
- [`get_vm_snapshots(vm_id)`](src/vmware_mcp/modules/snapshot.py:38) — Lists a VM's snapshots. Accepts the `id` from `list_vms`, resolves it to a `.vmx` path via `VMRestClient`, then queries via `VMCliClient`. **Registered with both clients: `register(client, vmcli)`.**

## Data Flow

### Standard REST flow (VM, Power, Health)
1. **Client → Server**: An MCP client sends a tool call over streamable-http to port 51001.
2. **Server → Module**: FastMCP routes the call to the registered tool function.
3. **Module → VMRestClient**: The tool uses the shared [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25).
4. **VMRestClient → vmrest**: Sends authenticated HTTP requests to `http://{host}:8697/api/vms/...`.
5. **Module → Response**: The tool serializes the response as a JSON string back to the MCP client.

### Snapshot flow (dual-client)
1. **Client → Server**: MCP client calls `get_vm_snapshots(vm_id)`.
2. **Resolve path**: The tool calls [`VMRestClient.get_vm_path(vm_id)`](src/vmware_mcp/vmrest_client.py:160) → hits `GET /api/vms`, matches by `id`, returns `.vmx` path.
3. **Query snapshots**: The tool calls [`VMCliClient.get_snapshots(vmx_path)`](src/vmware_mcp/vmcli_client.py:90) → runs `vmcli.exe snapshot <path> query --format json`.
4. **Parse & normalize**: Raw vmcli JSON is parsed into a [`SnapshotQueryResult`](src/vmware_mcp/models.py:50).
5. **Module → Response**: The tool returns a clean JSON string with `vm_id`, `vmx_path`, `current_uid`, `count`, and a `snapshots` array.

## Design Patterns

- **Module Pattern**: Domain tools are isolated in separate modules with a consistent `register(...)` + `tools` interface, enabling easy addition of new tool categories.
- **Lazy Singleton**: Both [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) and [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) are created once on first access via [`get_client()`](src/vmware_mcp/server.py:55) / [`get_vmcli()`](src/vmware_mcp/server.py:67) and shared across modules. They share a single loaded config.
- **Adapter / Dual-Backend**: Two client classes adapt two different transports (HTTP + subprocess) behind uniform, typed method interfaces. Modules choose the appropriate client(s).
- **Dataclass for Config, Pydantic for Data Models**: Configuration uses `@dataclass`; API/CLI response models use Pydantic `BaseModel`.
- **Error-as-Return**: Tools catch exceptions ([`VMRestClientError`](src/vmware_mcp/vmrest_client.py:17), [`VMCliError`](src/vmware_mcp/vmcli_client.py:26), `ValueError`) and return structured JSON error objects rather than propagating exceptions to the MCP client.
