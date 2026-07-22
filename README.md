# VMware MCP Server

MCP server for managing VMware Workstation virtual machines via the
`vmrest.exe` REST API.  Exposes VM lifecycle and snapshot operations as
MCP tools that can be consumed by any MCP-compatible AI assistant.

## Prerequisites

- **Python >= 3.11**
- **VMware Workstation Pro 17+** with the REST API service enabled
  (`vmrest.exe` running on port 8697 by default)
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

## Quick Start

```bash
# Clone / open the project directory
cd VMwareMCP

# Create a virtual environment and install
uv venv
uv pip install -e .

# Set at least one host (use your Windows credentials)
export VMREST_HOST_1=localhost
export VMREST_USERNAME_1=your_username
export VMREST_PASSWORD_1=your_password

# Run the server
uv run vmware-mcp
```

## Environment Variables

Each host uses a numbered suffix (`_1`, `_2`, …).  The server scans
sequentially and stops at the first missing `VMREST_HOST_N`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `VMREST_HOST_N` | **Yes** | — | Hostname or IP address |
| `VMREST_PORT_N` | No | `8697` | vmrest API port |
| `VMREST_USERNAME_N` | **Yes** | — | Windows username (Basic Auth) |
| `VMREST_PASSWORD_N` | **Yes** | — | Windows password (Basic Auth) |
| `VMREST_VERIFY_SSL_N` | No | `false` | Verify self-signed certificate |
| `VMREST_ALIAS_N` | No | `host-N` | Friendly name for this host |

### Example (two hosts)

```bash
# Host 1 – local workstation
export VMREST_HOST_1=localhost
export VMREST_USERNAME_1=Admin
export VMREST_PASSWORD_1=secret
export VMREST_ALIAS_1=my-pc

# Host 2 – remote dev server
export VMREST_HOST_2=192.168.1.100
export VMREST_USERNAME_2=Admin
export VMREST_PASSWORD_2=secret2
export VMREST_ALIAS_2=dev-server
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

## Project Structure

```
VMwareMCP/
├── src/vmware_mcp/
│   ├── server.py            # FastMCP server entry point
│   ├── client_manager.py    # Multi-host client pool
│   ├── vmrest_client.py     # HTTP client for single vmrest host
│   ├── models.py            # Pydantic data models
│   └── config.py            # Environment-based configuration
├── pyproject.toml
└── README.md
```

## License

MIT
