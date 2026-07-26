# 05 — Development Guidelines

## Project Identity

- **Name**: VMwareMCP (`vmware-mcp` on PyPI)
- **Version**: 0.1.0
- **License**: MIT
- **Language**: Python 3.11+
- **Package layout**: `src/vmware_mcp/` (src-layout)

## Code Style & Conventions

### Formatting & Linting
- Follow PEP 8 conventions.
- Use `ruff` for linting and formatting if available.
- Line length: no strict limit, but keep lines reasonable (< 120 chars preferred).

### Type Hints
- Use modern Python 3.11+ type syntax: `X | None` instead of `Optional[X]`.
- Always include `from __future__ import annotations` at the top of every module.
- Use type hints on all function signatures (parameters and return types).
- Use Pydantic `BaseModel` for API/CLI data models; use `@dataclass` for internal configuration.

### Naming Conventions
- **Files/modules**: `snake_case.py`
- **Classes**: `PascalCase` (e.g., `VMRestClient`, `VMCliClient`, `VMRestHostConfig`)
- **Functions/methods**: `snake_case` (e.g., `get_vm_details`, `power_operation`, `get_snapshots`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `VMREST_HOST`, `VMCLI_PATH`)
- **Private members**: prefix with `_` (e.g., `_client`, `_vmcli`, `_session`, `_run()`)
- **Exceptions**: `PascalCase` ending in `Error` (e.g., `VMRestClientError`, `VMCliError`)
- **Tool functions** (MCP-exposed): descriptive `snake_case` (e.g., `list_vms`, `set_vm_power_state`, `check_server_health`, `get_vm_snapshots`)

### Docstrings
- Use triple-quoted docstrings on all public classes, methods, and functions.
- MCP tool docstrings are critical — they serve as the tool description for AI agents. Include:
  - **When to use**: describe the scenarios where this tool is appropriate.
  - **How to use / Args**: document each parameter with its expected format (e.g., clarify whether to pass the `id` vs the `path`).
  - **Returns**: describe the JSON structure of the response.
  - **Example output**: include a JSON example where helpful.

### Import Style
- Use absolute imports: `from vmware_mcp.config import load_config`
- Group imports: stdlib → third-party → local (PEP 8 import ordering).
- Use `from __future__ import annotations` as the first import.

## Architecture Rules

### Choosing a Backend Client

There are **two** client layers. Pick the correct one for the operation:

- **[`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) (HTTP)** — Use for anything the vmrest REST API supports: listing, power, config, network, health. Works local or remote.
- **[`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) (subprocess)** — Use **only** for operations the REST API lacks (currently snapshot queries). **Local-only.** Always document the co-location requirement in the tool docstring.

A module may depend on both (see [`snapshot.py`](src/vmware_mcp/modules/snapshot.py): resolve id→path via REST, then query via vmcli).

### Adding a New Tool Module

1. Create `src/vmware_mcp/modules/<domain>.py`.
2. Define a module-level `tools = FastMCP("VMware <Domain>", instructions="...")`.
3. Implement a `register(...)` function that sets the module-level client reference(s) and defines `@tools.tool()` decorated functions. Accept whichever client(s) the module needs:
   - REST-only: `def register(client: VMRestClient)`
   - vmcli-only: `def register(vmcli: VMCliClient)`
   - Both: `def register(client: VMRestClient, vmcli: VMCliClient)`
4. In [`server.py`](src/vmware_mcp/server.py:82) `_register_modules()`, import the module, call its `register(...)` with the shared client(s) from [`get_client()`](src/vmware_mcp/server.py:55) / [`get_vmcli()`](src/vmware_mcp/server.py:67), then `mcp.mount(module.tools)` and log it.
5. All tool functions must return **JSON strings** (use `json.dumps`).
6. Catch backend exceptions (`VMRestClientError`, `VMCliError`, `ValueError`) and return structured JSON error objects — never let exceptions propagate to the MCP client.

### Adding a New REST Client Method

1. Add the method to [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) in `vmrest_client.py`.
2. URL-encode VM IDs using `quote(vm_id, safe="")` — VM IDs are opaque unique identifiers returned by `list_vms`.
3. Use `self._request(method, path, ...)` for all HTTP calls.
4. Return Pydantic models (not raw dicts) when the response has a well-defined schema.
5. **Remember:** the vmrest `id` and `path` are distinct. Do not assume `GET /api/vms/{id}` returns the path — use [`get_vm_path()`](src/vmware_mcp/vmrest_client.py:160) to resolve.

### Adding a New vmcli Operation

1. Add the method to [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) in `vmcli_client.py`.
2. Build the argument list and call `self._run([...])` — this handles binary-existence checks, timeout, and non-zero exit codes.
3. Parse `stdout` as JSON inside a `try/except json.JSONDecodeError`, raising [`VMCliError`](src/vmware_mcp/vmcli_client.py:26) with the raw output on failure.
4. Return a Pydantic model, not a raw dict.
5. Pass the `.vmx` **path** (not the `id`) to vmcli — resolve the id first in the calling tool.

### Data Flow Rule
- **Tool functions** → call client method(s) → format response as JSON string.
- **Never** make HTTP requests or spawn subprocesses directly from tool modules — always go through a client class.
- **Never** return raw dicts from tools — always serialize with `json.dumps`.

## Error Handling

- [`VMRestClientError`](src/vmware_mcp/vmrest_client.py:17) carries `status_code` and message.
- [`VMCliError`](src/vmware_mcp/vmcli_client.py:26) carries an optional `returncode` and an actionable message (e.g., how to set `VMCLI_PATH`).
- Tool functions should catch these and return `{"error": "...", "success": false, ...}` JSON.
- Tool functions should catch `ValueError` for input validation errors.
- **Prefer explicit `if x is None` guards over `assert`** for null checks in tool functions — `assert` is stripped under `python -O`. See [`health.py`](src/vmware_mcp/modules/health.py:59) for the preferred pattern. (Some older tools still use `assert`; migrate them when touched.)
- Make error messages **actionable** — tell the agent how to fix the problem (e.g., "Pass the 'id' field from list_vms", "Set the VMCLI_PATH environment variable").

## Logging

- All logging goes to **stderr** via [`logging.basicConfig(stream=sys.stderr)`](src/vmware_mcp/server.py:21).
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Logger names: `"vmware_mcp"` (root), `"vmware_mcp.vmcli"` (vmcli client), sub-loggers per module as needed.
- Use `logger.info()` for normal operations, `logger.error()` for failures.
- **Critical**: Never use `print()` or `sys.stdout` — this corrupts JSON-RPC messages in stdio mode.

## Git Workflow

### Branch Naming
- `main` — stable, production-ready code.
- `feature/<description>` — new features (e.g., `feature/snapshot-tools`).
- `fix/<description>` — bug fixes.
- `refactor/<description>` — code refactoring.

### Commit Messages
- Use imperative mood: "Add snapshot tools" not "Added snapshot tools".
- Format: `<type>: <description>`
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
- Example: `feat: add get_vm_snapshots MCP tool backed by vmcli`

### `.gitignore` Rules
The following are ignored (see [`.gitignore`](.gitignore)):
- `plans/architecture.md` — scratch planning notes
- `vmware_mcp.egg-info/` — build artifacts
- `__pycache__/` — bytecode
- `uv.lock` — lock file
- `.env` — credentials
- `.roo/rules/mcp-build-rule.md` — internal rules

## Testing Strategy (Planned)

- **Unit tests (REST)**: Mock `requests.Session` to test [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) methods in isolation.
- **Unit tests (vmcli)**: Mock `subprocess.run` and `pathlib.Path.is_file` to test [`VMCliClient`](src/vmware_mcp/vmcli_client.py:34) — cover success, missing binary, non-zero exit, timeout, and malformed JSON.
- **Integration tests**: Test tool functions with mocked clients, asserting the JSON string shape (including error paths).
- **No E2E tests**: Would require a running VMware Workstation instance.
- Framework: `pytest` with `pytest-mock` for mocking.

## Key Reminders

- The `instructions` parameter on `FastMCP` instances is how AI agents discover what each tool does — write them carefully.
- VM IDs are **opaque unique identifiers** returned by `list_vms` — pass them exactly as received. The `id` and `path` are **different values**; use [`get_vm_path()`](src/vmware_mcp/vmrest_client.py:160) to convert.
- Snapshot tools are **local-only** (they invoke `vmcli.exe`). Always state this in tool docstrings.
- The project uses **src-layout** — the package lives under `src/vmware_mcp/`, not at the project root.
- Keep this `/project-knowledge` directory up to date — it is the mandatory pre-flight read for any new session (see `.roo/rules`).
