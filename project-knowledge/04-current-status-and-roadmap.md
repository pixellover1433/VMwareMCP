# 04 — Current Status & Roadmap

## Version: 0.1.0

## Recent Major Changes

- **Initial MCP server implementation** — Complete working server with FastMCP framework, streamable-http transport on port 51001.
- **VM tools** — [`list_vms()`](src/vmware_mcp/modules/vm.py:30) and [`get_vm_details()`](src/vmware_mcp/modules/vm.py:82) with power state and IP enrichment.
- **Power tools** — [`get_vm_power_state()`](src/vmware_mcp/modules/power.py:29) and [`set_vm_power_state()`](src/vmware_mcp/modules/power.py:56) supporting 6 power operations (on, off, shutdown, suspend, pause, unpause).
- **Snapshot tools removed** — Snapshot MCP tools were intentionally removed from [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py). The client methods still exist in [`vmrest_client.py`](src/vmware_mcp/vmrest_client.py:202) but are not exposed as MCP tools.
- **Module architecture** — Each domain (vm, power, snapshot) is a separate FastMCP instance mounted on the main server, providing clean separation.

## Current Capabilities

| Tool | Status | Description |
|---|---|---|
| `list_vms` | ✅ Working | Lists all VMs with id, path, name, power state, and IP |
| `get_vm_details` | ✅ Working | Returns detailed config, power state, and network info |
| `get_vm_power_state` | ✅ Working | Returns current power state of a VM |
| `set_vm_power_state` | ✅ Working | Performs power operations (on/off/suspend/shutdown/pause/unpause). Sends the operation as a plain-text body (e.g. `on`) via PUT to vmrest. Returns JSON with `power_state`, `success`, and `error` fields. |
| Snapshot tools | ❌ Removed | Client methods exist but MCP tools are not exposed |

## Known Issues & Technical Debt

1. **Snapshot module is empty** — [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py) is a placeholder. The snapshot client methods in [`vmrest_client.py`](src/vmware_mcp/vmrest_client.py:202) (`get_snapshots`, `create_snapshot`, `delete_snapshot`, `revert_snapshot`) are implemented but not wired to MCP tools.
2. **No tests** — The project has no unit or integration tests. The `vmrest_client.py` and module logic are untested.
3. **No error handling for missing displayName** — [`get_vms()`](src/vmware_mcp/vmrest_client.py:96) calls [`get_vm_param()`](src/vmware_mcp/vmrest_client.py:77) for each VM to get `displayName`, resulting in N+1 API calls. This could be slow for hosts with many VMs.
4. **Module uses assert for null checks** — Tools use `assert _client is not None` which would be stripped in optimized mode (`python -O`). Should use proper runtime checks.
5. **No retry logic** — [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) has no retry mechanism for transient network failures.
6. **Single-host only** — The server connects to exactly one `vmrest.exe` instance. Multi-host support is not implemented.
7. **No graceful shutdown** — The server does not call [`VMRestClient.close()`](src/vmware_mcp/vmrest_client.py:256) on exit.
8. **Hardcoded transport/port** — Port 51001 and streamable-http transport are hardcoded in [`main()`](src/vmware_mcp/server.py:94).

## Immediate Next Steps

- [ ] Re-implement snapshot MCP tools (list, create, delete, revert) in [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py).
- [ ] Add unit tests for [`vmrest_client.py`](src/vmware_mcp/vmrest_client.py) (mock HTTP) and module tools.
- [ ] Replace `assert` with proper runtime validation in tool functions.
- [ ] Add configurable port and transport via environment variables.
- [ ] Implement graceful shutdown with client cleanup.
- [ ] Add retry logic with exponential backoff to [`VMRestClient._request()`](src/vmware_mcp/vmrest_client.py:47).
- [ ] Consider adding `vmx_path` listing optimization to avoid N+1 queries.

## Future Considerations

- Multi-host support (multiple `vmrest.exe` instances).
- VM creation and deletion tools.
- Guest OS command execution (if vmrest supports it).
- Metrics / observability integration.
- Docker containerization for deployment.
