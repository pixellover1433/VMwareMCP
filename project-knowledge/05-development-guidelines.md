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
- Use Pydantic `BaseModel` for API data models; use `@dataclass` for internal configuration.

### Naming Conventions
- **Files/modules**: `snake_case.py`
- **Classes**: `PascalCase` (e.g., `VMRestClient`, `VMRestHostConfig`)
- **Functions/methods**: `snake_case` (e.g., `get_vm_details`, `power_operation`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `VMREST_HOST`)
- **Private members**: prefix with `_` (e.g., `_client`, `_session`, `_url()`)
- **Tool functions** (MCP-exposed): descriptive `snake_case` (e.g., `list_vms`, `set_vm_power_state`)

### Docstrings
- Use triple-quoted docstrings on all public classes, methods, and functions.
- MCP tool docstrings are critical — they serve as the tool description for AI agents. Include:
  - **When to use**: describe the scenarios where this tool is appropriate.
  - **Args**: document each parameter with its expected format.
  - **Returns**: describe the JSON structure of the response.
  - **Example output**: include a JSON example where helpful.

### Import Style
- Use absolute imports: `from vmware_mcp.config import load_config`
- Group imports: stdlib → third-party → local (PEP 8 import ordering).
- Use `from __future__ import annotations` as the first import.

## Architecture Rules

### Adding a New Tool Module

1. Create `src/vmware_mcp/modules/<domain>.py`.
2. Define a module-level `tools = FastMCP("VMware <Domain>", instructions="...")`.
3. Implement a `register(client: VMRestClient)` function that sets the module-level `_client` and defines `@tools.tool()` decorated functions.
4. In [`server.py`](src/vmware_mcp/server.py:67), import the module and call:
   ```python
   from vmware_mcp.modules import new_module
   new_module.register(client)
   mcp.mount(new_module.tools)
   ```
5. All tool functions must return **JSON strings** (use `json.dumps`).
6. Catch all `VMRestClientError` exceptions and return structured JSON error objects — never let exceptions propagate to the MCP client.

### Adding a New Client Method

1. Add the method to [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) in `vmrest_client.py`.
2. URL-encode VM IDs using `quote(vm_id, safe="")` — VM IDs are opaque unique identifiers returned by `list_vms` (internally they map to VMX paths in the vmrest API, but treat them as opaque strings).
3. Use `self._request(method, path, ...)` for all HTTP calls.
4. Return Pydantic models (not raw dicts) when the response has a well-defined schema.

### Data Flow Rule
- **Tool functions** → call `VMRestClient` methods → format response as JSON string.
- **Never** make HTTP requests directly from tool modules.
- **Never** return raw dicts from tools — always serialize with `json.dumps`.

## Error Handling

- [`VMRestClientError`](src/vmware_mcp/vmrest_client.py:17) carries `status_code` and message.
- Tool functions should catch `VMRestClientError` and return `{"error": "...", "success": false}` JSON.
- Tool functions should catch `ValueError` for input validation errors.
- Use `logging` (to stderr) for operational logs — **never print to stdout** (corrupts stdio transport).

## Logging

- All logging goes to **stderr** via [`logging.basicConfig(stream=sys.stderr)`](src/vmware_mcp/server.py:20).
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Logger name: `"vmware_mcp"` (root), sub-loggers for modules.
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
- Example: `feat: add list_snapshots MCP tool to snapshot module`

### `.gitignore` Rules
The following are ignored (see [`.gitignore`](.gitignore)):
- `plans/architecture.md` — scratch planning notes
- `vmware_mcp.egg-info/` — build artifacts
- `__pycache__/` — bytecode
- `uv.lock` — lock file
- `.env` — credentials
- `.roo/rules/mcp-build-rule.md` — internal rules

## Testing Strategy (Planned)

- **Unit tests**: Mock `requests.Session` to test [`VMRestClient`](src/vmware_mcp/vmrest_client.py:25) methods in isolation.
- **Integration tests**: Test tool functions with a mocked client.
- **No E2E tests**: Would require a running VMware Workstation instance.
- Framework: `pytest` with `pytest-mock` for mocking.

## Key Reminders

- The `instructions` parameter on `FastMCP` instances is how AI agents discover what each tool does — write them carefully.
- VM IDs are **opaque unique identifiers** returned by `list_vms` — always pass them exactly as received to other tools. Always URL-encode them when used in REST API paths.
- The project uses **src-layout** — the package lives under `src/vmware_mcp/`, not at the project root.
