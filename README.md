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

### Example

```bash
# Using a .env file (copy .env.example to .env)
VMREST_HOST=localhost
VMREST_PORT=8697
VMREST_USERNAME=Admin
VMREST_PASSWORD=secret
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
│   ├── vmrest_client.py     # HTTP client for vmrest host
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Environment-based configuration
│   └── modules/
│       ├── vm.py            # VM list and detail tools
│       └── snapshot.py      # Snapshot tools (placeholder)
├── pyproject.toml
└── README.md
```

## License

MIT
