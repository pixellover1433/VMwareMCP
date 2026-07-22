"""VMware MCP Server - FastMCP entry point.

Creates the FastMCP server instance and wires up the multi-host client
manager. MCP tools will be added separately as requested.
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

# ---------------------------------------------------------------------------
# Client manager (loaded at import time so tools can reference it)
# ---------------------------------------------------------------------------
client_manager: VMRestClientManager | None = None


def get_client_manager() -> VMRestClientManager:
    """Return the global client manager, initialising it lazily."""
    global client_manager
    if client_manager is None:
        client_manager = VMRestClientManager()
        if not client_manager.aliases:
            logger.warning(
                "No VMware hosts configured. "
                "Set VMREST_HOST_1, VMREST_HOST_2, etc. environment variables."
            )
    return client_manager


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server.

    By default FastMCP uses the httpStreamable transport on port 51001.
    You can override the transport with the --transport flag or by setting
    the FASTMCP_TRANSPORT env var.
    """
    get_client_manager()
    mcp.run()


if __name__ == "__main__":
    main()
