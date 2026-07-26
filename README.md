# VMware MCP Server

MCP server for managing VMware Workstation virtual machines. It exposes VM
lifecycle, power, health, and snapshot operations as MCP tools that can be
consumed by any MCP-compatible AI assistant.

It talks to VMware Workstation through **two backends**:

- **`vmrest.exe` (HTTP REST API)** — used for listing VMs, power control,
  configuration, network info, and health checks. Can be local or remote.
- **`vmcli.exe` (local binary)** — used for snapshot queries, which the REST
  API does not expose. **Local-only:** snapshot tools require the server to run
  on the same host as VMware Workstation.

## Available Tools

| Tool | Backend | Description |
|---|---|---|
| `list_vms` | vmrest | List all VMs with id, path, name, power state, and IP |
| `get_vm_details` | vmrest | Detailed config, power state, and network info for a VM |
| `get_vm_power_state` | vmrest | Current power state of a VM |
| `set_vm_power_state` | vmrest | Power operations: on, off, shutdown, suspend, pause, unpause |
| `check_server_health` | vmrest | Verify the server can reach and authenticate against vmrest |
| `get_vm_snapshots` | vmcli | List a VM's snapshots (uid, name, parent, current). Local-only. |

## Prerequisites

- **Python >= 3.11**
- **VMware Workstation Pro 17+** with the REST API service enabled
  (`vmrest.exe` running on port 8697 by default)
- **`vmcli.exe`** (bundled with VMware Workstation) — required only for the
  snapshot tool, and only when the server runs on the same host as Workstation
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

## Quick Start

```bash
# Clone / open the project directory
cd VMwareMCP

# Create a virtual environment and install
uv venv
uv pip install -e .

# Configure the vmrest host (use your Windows credentials)
export VMREST_HOST=localhost
export VMREST_USERNAME=your_username
export VMREST_PASSWORD=your_password

# Run the server
uv run vmware-mcp
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `VMREST_HOST` | **Yes** | — | Hostname or IP address of the vmrest host |
| `VMREST_PORT` | No | `8697` | vmrest API port |
| `VMREST_USERNAME` | **Yes** | — | Windows username (Basic Auth) |
| `VMREST_PASSWORD` | **Yes** | — | Windows password (Basic Auth) |
| `VMREST_VERIFY_SSL` | No | `false` | Verify self-signed certificate |
| `VMCLI_PATH` | No | `C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe` | Path to `vmcli.exe`. Only used by the snapshot tool. Override if VMware is installed elsewhere. |

### Example

```bash
# Using a .env file (copy .env.example to .env)
VMREST_HOST=localhost
VMREST_PORT=8697
VMREST_USERNAME=Admin
VMREST_PASSWORD=secret
VMCLI_PATH=C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe
```

## Transport

The server defaults to **streamable-http** on **port 51001**.

- Server URL: `http://localhost:51001/mcp`
- Override with `--transport stdio` for stdio mode

## MCP Client Configuration

### streamable-http (default)

```json
{
  "mcpServers": {
    "vmware": {
      "url": "http://localhost:51001/mcp"
    }
  }
}
```

### stdio

```json
{
  "mcpServers": {
    "vmware": {
      "command": "uv",
      "args": ["run", "vmware-mcp", "--transport", "stdio"]
    }
  }
}
```

## Verifying the Setup

1. Ensure `vmrest.exe` is running: browse to `http://localhost:8697/api/vms`.
2. Start the server: `uv run vmware-mcp`.
3. Connect your MCP client to `http://localhost:51001/mcp`.
4. Call `check_server_health` first — it confirms connectivity and auth before
   you run other operations.

## Notes on IDs vs Paths

- `list_vms` returns both an opaque `id` and the `.vmx` filesystem `path`.
- Pass the **`id`** to all tools (including `get_vm_snapshots`). The snapshot
  tool automatically resolves the `id` to the `.vmx` path via the vmrest API
  before invoking `vmcli.exe` — you never need to supply a path manually.

## Project Structure

```
VMwareMCP/
├── src/vmware_mcp/
│   ├── server.py            # FastMCP server entry point + client accessors
│   ├── vmrest_client.py     # HTTP client for the vmrest REST API
│   ├── vmcli_client.py      # Subprocess client for the local vmcli.exe binary
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Environment-based configuration
│   └── modules/
│       ├── vm.py            # VM list and detail tools
│       ├── power.py         # Power state query and control tools
│       ├── health.py        # Server/backend health check tool
│       └── snapshot.py      # Snapshot listing tool (via vmcli)
├── project-knowledge/       # Detailed architecture & contributor docs
├── pyproject.toml
└── README.md
```

For deeper architecture, setup, and contribution details, see the
[`project-knowledge/`](project-knowledge) directory.

## License

MIT
