"""VMware MCP Server - FastMCP entry point.

Creates the FastMCP server instance, loads the vmrest client,
and registers domain-specific tool modules (vm).
"""

from __future__ import annotations

import logging
import sys

from fastmcp import FastMCP

from vmware_mcp.config import VMRestHostConfig, load_config
from vmware_mcp.vmrest_client import VMRestClient

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("vmware_mcp")

# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "VMware MCP Server",
    instructions="""Use this server to manage VMware Workstation virtual machines on
a local or remote Windows host via the vmrest REST API.

When to use this server:
- The user wants to list VMs registered on the configured host.
- The user needs details about a specific VM (power state, hardware config, network).
- The user wants to power on, off, suspend, pause, or otherwise control a VM.

Capabilities provided by mounted tool modules:
- VMs: list VMs and get VM details (config, network, power state).
- Power: query and control VM power state (on, off, suspend, shutdown, pause, unpause).
""",
)

# Module-level client (initialised in main)
_client: VMRestClient | None = None
_config: VMRestHostConfig | None = None


def get_client() -> VMRestClient:
    """Return the global vmrest client, initialising it lazily."""
    global _client, _config
    if _client is None:
        _config = load_config()
        _client = VMRestClient(_config)
        logger.info(
            "Connected to vmrest at %s:%d", _config.host, _config.port
        )
    return _client


# ---------------------------------------------------------------------------
# Tool module registration
# ---------------------------------------------------------------------------

def _register_modules() -> None:
    """Import each tool module, register its tools, and mount it."""
    from vmware_mcp.modules import power, vm

    client = get_client()

    vm.register(client)
    mcp.mount(vm.tools)
    logger.info("Mounted tool module: vm")

    power.register(client)
    mcp.mount(power.tools)
    logger.info("Mounted tool module: power")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server with streamable-http transport on port 51001.

    Override with:
        uv run vmware-mcp --transport stdio
    """
    get_client()
    _register_modules()
    mcp.run(transport="streamable-http", port=51001)


if __name__ == "__main__":
    main()
