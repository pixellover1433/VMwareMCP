"""VMware MCP Server - FastMCP entry point.

Creates the FastMCP server instance, loads the multi-host client manager,
and registers domain-specific tool modules (host, vm, snapshot).
"""

from __future__ import annotations

import logging
import sys

from fastmcp import FastMCP

from vmware_mcp.client_manager import VMRestClientManager

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
mcp = FastMCP("VMware MCP Server")

# Module-level client manager (initialised in main)
_manager: VMRestClientManager | None = None


def get_client_manager() -> VMRestClientManager:
    """Return the global client manager, initialising it lazily."""
    global _manager
    if _manager is None:
        _manager = VMRestClientManager()
        if not _manager.aliases:
            logger.warning(
                "No VMware hosts configured. "
                "Set VMREST_HOST_1, VMREST_HOST_2, etc. environment variables."
            )
    return _manager


# ---------------------------------------------------------------------------
# Tool module registration
# ---------------------------------------------------------------------------

def _register_modules() -> None:
    """Import each tool module, register its tools, and mount it."""
    from vmware_mcp.modules import host, vm, snapshot

    manager = get_client_manager()

    modules = [host, vm, snapshot]
    for mod in modules:
        mod.register(manager)
        mcp.mount(mod.tools)
        logger.info("Mounted tool module: %s", mod.__name__.split(".")[-1])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server with streamable-http transport on port 51001.

    Override with:
        uv run vmware-mcp --transport stdio
    """
    get_client_manager()
    _register_modules()
    mcp.run(transport="streamable-http", port=51001)


if __name__ == "__main__":
    main()
