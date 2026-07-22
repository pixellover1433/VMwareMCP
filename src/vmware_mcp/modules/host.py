"""Host management MCP tools.

Tools for listing and inspecting configured vmrest hosts.
"""

from __future__ import annotations

from fastmcp import FastMCP

from vmware_mcp.client_manager import VMRestClientManager
from vmware_mcp.models import HostInfo, ListHostsResponse
from vmware_mcp.vmrest_client import VMRestClientError

tools = FastMCP("VMware Hosts")


def register(manager: VMRestClientManager) -> None:
    """Register host tools with the given client manager."""

    @tools.tool()
    def list_hosts() -> str:
        """List all configured vmrest hosts and their connection status.

        Returns JSON with a list of hosts, each including alias, host address,
        port, base_url, reachable status, and index.
        """
        hosts = manager.list_hosts()
        response = ListHostsResponse(hosts=hosts, total=len(hosts))
        return response.model_dump_json(indent=2)
