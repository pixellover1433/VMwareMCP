# 04 — Current Status & Roadmap

## Version: 0.1.0

## Recent Major Changes

- **Health check tool added** — New [`modules/health.py`](src/vmware_mcp/modules/health.py) with [`check_server_health()`](src/vmware_mcp/modules/health.py:30). Lets agents verify the server can reach and authenticate against the vmrest backend before running other operations. Backed by [`VMRestClient.health_check()`](src/vmware_mcp/vmrest_client.py:77).
- **Snapshot listing via vmcli** — [`modules/snapshot.py`](src/vmware_mcp/modules/snapshot.py) now exposes [`get_vm_snapshots(vm_id)`](src/vmware_mcp/modules/snapshot.py:38). Because the vmrest REST API does not expose snapshot queries, this uses a new subprocess client, [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34), to invoke the local `vmcli.exe`.
- **New subprocess client layer** — [`vmcli_client.py`](src/vmware_mcp/vmcli_client.py) wraps `vmcli.exe` with timeout handling, binary-existence checks, and a dedicated [`VMCliError`](src/vmware_mcp/vmcli_client.py:26) exception.
- **ID → path resolution** — Added [`VMRestClient.get_vm_path()`](src/vmware_mcp/vmrest_client.py:160). The vmrest `id` and `path` are distinct, and `GET /api/vms/{id}` does not return the path; this method queries `GET /api/vms` and matches by `id` to obtain the `.vmx` path. The snapshot tool accepts the same `id` returned by `list_vms` and resolves it internally.
- **Configurable vmcli path** — [`config.py`](src/vmware_mcp/config.py:35) now includes a `vmcli_path` field (env var `VMCLI_PATH`, defaulting to the standard Workstation install location).
- **Snapshot models reworked** — [`models.py`](src/vmware_mcp/models.py) replaced the old REST-based `Snapshot` model with vmcli-oriented [`Snapshot`](src/vmware_mcp/models.py:35) (uid, name, parent_uid, is_current) and [`SnapshotQueryResult`](src/vmware_mcp/models.py:50).

## Current Capabilities

| Tool | Module | Backend | Status | Description |
|---|---|---|---|---|
| `list_vms` | vm | vmrest | ✅ Working | Lists all VMs with id, path, name, power state, and IP |
| `get_vm_details` | vm | vmrest | ✅ Working | Returns detailed config, power state, and network info |
| `get_vm_power_state` | power | vmrest | ✅ Working | Returns current power state of a VM |
| `set_vm_power_state` | power | vmrest | ✅ Working | Power operations (on/off/suspend/shutdown/pause/unpause). Sends the operation as a plain-text body via PUT. Returns JSON with `power_state`, `success`, `error`. |
| `check_server_health` | health | vmrest | ✅ Working | Reports whether the vmrest backend is reachable and authenticating. Returns `status`, `reachable`, `base_url`, `vm_count`. |
| `get_vm_snapshots` | snapshot | vmcli (+ vmrest for id→path) | ✅ Working | Lists a VM's snapshots (uid, name, parent_uid, is_current) by invoking local `vmcli.exe`. Requires server co-located with VMware Workstation. |

## Known Issues & Technical Debt

1. **Snapshot tools are local-only** — [`get_vm_snapshots`](src/vmware_mcp/modules/snapshot.py:38) shells out to `vmcli.exe`, so it fails when the server runs on a different host than VMware Workstation (returns an actionable `vmcli.exe not found` error). Remote snapshot support would require a different mechanism.
2. **N+1 API calls for listing** — [`get_vms()`](src/vmware_mcp/vmrest_client.py:135) calls [`get_vm_param()`](src/vmware_mcp/vmrest_client.py:116) per VM for `displayName`, and [`list_vms`](src/vmware_mcp/modules/vm.py:30) further calls power/nic endpoints per VM. Slow for hosts with many VMs.
3. **Redundant id→path lookup** — [`get_vm_path()`](src/vmware_mcp/vmrest_client.py:160) fetches the full VM list on every snapshot call. Could be cached.
4. **Unused REST snapshot methods** — [`create_snapshot()`](src/vmware_mcp/vmrest_client.py:282), [`delete_snapshot()`](src/vmware_mcp/vmrest_client.py:303), [`revert_snapshot()`](src/vmware_mcp/vmrest_client.py:309), and REST [`get_snapshots()`](src/vmware_mcp/vmrest_client.py:263) exist but are not wired to any MCP tool (and the REST `get_snapshots` uses the older `Snapshot` field shape).
5. **No tests** — No unit or integration tests exist for either client or the modules.
6. **Modules use `assert` for null checks** — Tools use `assert _client is not None`, which is stripped under `python -O`. Should use proper runtime checks. (Note: [`health.py`](src/vmware_mcp/modules/health.py:59) already uses a proper `if _client is None` guard — a good pattern to replicate.)
7. **No retry logic** — [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) has no retry mechanism for transient network failures.
8. **Single-host only** — The server connects to exactly one `vmrest.exe` instance.
9. **No graceful shutdown** — The server does not call [`VMRestClient.close()`](src/vmware_mcp/vmrest_client.py:317) on exit.
10. **Hardcoded transport/port** — Port 51001 and streamable-http transport are hardcoded in [`main()`](src/vmware_mcp/server.py:110).

## Immediate Next Steps

- [ ] Add unit tests: mock `requests.Session` for [`VMRestClient`](src/vmware_mcp/vmrest_client.py), and mock `subprocess.run` for [`VMCliClient`](src/vmware_mcp/vmcli_client.py).
- [ ] Replace `assert` with proper runtime validation in tool functions (follow the [`health.py`](src/vmware_mcp/modules/health.py:59) pattern).
- [ ] Cache the VM id→path map to avoid repeated `GET /api/vms` on snapshot calls.
- [ ] Consider exposing snapshot create/delete/revert operations (via vmcli, for consistency with the query path).
- [ ] Add configurable port and transport via environment variables.
- [ ] Implement graceful shutdown with client cleanup.
- [ ] Add retry logic with exponential backoff to [`VMRestClient._request()`](src/vmware_mcp/vmrest_client.py:47).

## Future Considerations

- Multi-host support (multiple `vmrest.exe` instances).
- VM creation and deletion tools.
- Guest OS command execution (if supported by vmrest/vmcli).
- Metrics / observability integration.
- Docker containerization (note: snapshot tools would not work in a container unless VMware + vmcli are accessible inside it).
