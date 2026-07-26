"""Health check MCP tools.

Tools for verifying that the MCP server can reach and authenticate against
the vmrest.exe REST API.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.vmrest_client import VMRestClient, VMRestClientError

tools = FastMCP(
    "VMware Health",
    instructions="Use this module to verify that the MCP server is running and able to reach the vmrest backend. Use check_server_health as a diagnostic before other operations to confirm connectivity and authentication.",
)

# Module-level client reference (set during register)
_client: VMRestClient | None = None


def register(client: VMRestClient) -> None:
    """Register health tools with the given client."""
    global _client
    _client = client

    @tools.tool()
    def check_server_health() -> str:
        """Check the health and connectivity of the VMware MCP server.

        When to use:
        - Use as a first diagnostic step when VM operations are failing.
        - Use to confirm the vmrest backend is reachable and credentials are valid.
        - Use to verify the server is configured and responding before starting work.

        This tool sends a lightweight authenticated request to the vmrest API
        and reports whether the backend is reachable.

        Returns a JSON object with:
        - ``status``: "healthy" if vmrest is reachable, otherwise "unhealthy".
        - ``reachable``: true if the vmrest backend responded successfully.
        - ``base_url``: the configured vmrest base URL.
        - ``vm_count``: number of registered VMs (only when reachable, otherwise null).
        - ``status_code``: HTTP status code returned on failure (or null).
        - ``error``: error message on failure, or null when healthy.

        Example healthy output:
            {
              "status": "healthy",
              "reachable": true,
              "base_url": "http://127.0.0.1:8697",
              "vm_count": 3,
              "status_code": null,
              "error": null
            }
        """
        if _client is None:
            return json.dumps({
                "status": "unhealthy",
                "reachable": False,
                "base_url": None,
                "vm_count": None,
                "status_code": None,
                "error": "MCP server client is not initialised.",
            }, indent=2)

        try:
            health = _client.health_check()
        except VMRestClientError as exc:
            return json.dumps({
                "status": "unhealthy",
                "reachable": False,
                "base_url": None,
                "vm_count": None,
                "status_code": exc.status_code,
                "error": str(exc),
            }, indent=2)

        result = {
            "status": "healthy" if health.get("reachable") else "unhealthy",
            "reachable": health.get("reachable", False),
            "base_url": health.get("base_url"),
            "vm_count": health.get("vm_count"),
            "status_code": health.get("status_code"),
            "error": health.get("error"),
        }
        return json.dumps(result, indent=2)
