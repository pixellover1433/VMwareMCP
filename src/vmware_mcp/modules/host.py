"""Host management MCP tools.

Tools for listing and inspecting configured vmrest hosts.
"""

from __future__ import annotations

from fastmcp import FastMCP

from vmware_mcp.client_manager import VMRestClientManager
from vmware_mcp.models import HostInfo, ListHostsResponse

tools = FastMCP(
    "VMware Hosts",
    instructions="Use this module to discover which VMware Workstation vmrest hosts are configured and whether they are reachable. Always call list_hosts first before using any VM tools so you know which host aliases/numbers are available.",
)


def register(manager: VMRestClientManager) -> None:
    """Register host tools with the given client manager."""

    @tools.tool()
    def list_hosts() -> str:
        """List all configured vmrest hosts and their connection status.

        When to use:
        - Always call this FIRST before any VM tool to discover available hosts.
        - Use when the user asks which VMware hosts are configured or available.
        - Use to check if a host is reachable before performing VM operations.

        Returns a JSON object with:
        - ``hosts``: array of host objects, each with:
          ``alias`` (friendly name), ``host`` (IP/hostname), ``port``,
          ``base_url``, ``reachable`` (bool connectivity check), ``index`` (1-based number).
        - ``total``: total number of configured hosts.

        Example output:
        ```json
        {
          "hosts": [
            {
              "alias": "workstation-1",
              "host": "192.168.1.100",
              "port": 443,
              "base_url": "https://192.168.1.100:443",
              "reachable": true,
              "index": 1
            }
          ],
          "total": 1
        }
        ```

        No arguments required.
        """
        hosts = manager.list_hosts()
        response = ListHostsResponse(hosts=hosts, total=len(hosts))
        return response.model_dump_json(indent=2)
