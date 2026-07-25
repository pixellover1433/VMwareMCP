# 03 — Setup & Commands

## Prerequisites

1. **Python >= 3.11** — must be available on PATH.
2. **VMware Workstation Pro 17+** — installed on the target Windows host with the REST API service enabled.
3. **vmrest.exe** — must be running on port 8697 (default). Start it from VMware Workstation's installation directory.
4. **uv** (recommended) — fast Python package manager. Install via `pip install uv` or see [uv docs](https://docs.astral.sh/uv/). Alternatively, use standard `pip`.

## Local Environment Setup

```bash
# 1. Clone or open the project directory
cd VMwareMCP

# 2. Create a virtual environment
uv venv

# 3. Install the project in editable mode (includes all dependencies)
uv pip install -e .

# 4. Create a .env file from the template
cp .env.example .env
# Then edit .env with your actual vmrest credentials
```

## Environment Variables

All variables are read from `.env` (project root) or the shell environment.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VMREST_HOST` | **Yes** | — | Hostname or IP of the machine running `vmrest.exe` |
| `VMREST_PORT` | No | `8697` | Port that `vmrest.exe` listens on |
| `VMREST_USERNAME` | **Yes** | — | Windows username for Basic Auth |
| `VMREST_PASSWORD` | **Yes** | — | Windows password for Basic Auth |
| `VMREST_VERIFY_SSL` | No | `false` | Set to `true` to verify the self-signed SSL certificate |

**Never commit `.env` to version control** — it is in [`.gitignore`](.gitignore).

## Running the Server

```bash
# Streamable HTTP mode (default) — runs on port 51001
uv run vmware-mcp

# Stdio mode — for MCP clients that prefer stdio transport
uv run vmware-mcp --transport stdio

# Alternative: run directly with Python
python -m vmware_mcp.server
```

## MCP Client Configuration

### Streamable HTTP (default)

```json
{
  "mcpServers": {
    "vmware": {
      "url": "http://localhost:51001/mcp"
    }
  }
}
```

### Stdio

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

## Development Commands

```bash
# Install in editable mode (pick up code changes without reinstalling)
uv pip install -e .

# Run the server for testing
uv run vmware-mcp

# Run with stdio transport
uv run vmware-mcp --transport stdio

# Type checking (if mypy is installed)
mypy src/vmware_mcp/

# Linting (if ruff is installed)
ruff check src/
ruff format src/
```

## Verifying the Setup

1. Ensure `vmrest.exe` is running: open a browser to `http://localhost:8697/api/vms` — you should get a JSON response (may prompt for credentials).
2. Start the MCP server: `uv run vmware-mcp`.
3. Connect an MCP client (e.g., Claude Desktop, Roo Code) to `http://localhost:51001/mcp`.
4. The client should see tools: `list_vms`, `get_vm_details`, `get_vm_power_state`, `set_vm_power_state`.

## Troubleshooting

| Issue | Solution |
|---|---|
| `VMREST_HOST environment variable is not set` | Create a `.env` file or set the variable in your shell. |
| `Connection refused` on port 51001 | Ensure the server is running. Check for port conflicts. |
| `Connection refused` on port 8697 | Ensure `vmrest.exe` is running. Start it from VMware Workstation. |
| `401 Unauthorized` | Check `VMREST_USERNAME` and `VMREST_PASSWORD` match your Windows credentials. |
| `SSL certificate verify failed` | Set `VMREST_VERIFY_SSL=false` (default) or properly configure certificates. |
