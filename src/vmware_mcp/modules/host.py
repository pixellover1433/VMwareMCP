"""Host management MCP tools.

Tools for listing and inspecting configured vmrest hosts.
"""

from __future__ import annotations

from fastmcp import FastMCP

from vmware_mcp.client_manager import VMRestClientManager
from vmware_mcp.vmrest_client import VMRestClientError

tools = FastMCP("VMware Hosts")


def register(manager: VMRestClientManager) -> None:
    """Register host tools with the given client manager."""

    @tools.tool()
    def list_hosts() -> str:
        """List all configured vmrest hosts and their connection status.

        Returns a formatted table showing each host's alias, address,
        port, and whether it is reachable.
        """
        hosts = manager.list_hosts()
        if not hosts:
            return "No VMware hosts configured. Set VMREST_HOST_1, VMREST_HOST_2, etc."

        lines = ["Configured VMware Hosts:", ""]
        lines.append(f"{'Alias':<20} {'Address':<22} {'Port':<6} {'Reachable'}")
        lines.append("-" * 60)
        for h in hosts:
            status = "✓ Yes" if h.reachable else "✗ No"
            lines.append(f"{h.alias:<20} {h.host:<22} {h.port:<6} {status}")

        lines.append("")
        lines.append(f"Total: {len(hosts)} host(s)")
        return "\n".join(lines)
