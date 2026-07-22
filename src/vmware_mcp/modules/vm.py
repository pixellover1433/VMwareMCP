"""VM management MCP tools.

Tools for listing and inspecting virtual machines.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.client_manager import HostNotFoundError, VMRestClientManager
from vmware_mcp.vmrest_client import VMRestClientError

tools = FastMCP(
    "VMware VMs",
    instructions="Use this module to list virtual machines and inspect their configuration. Always call list_hosts first to discover available hosts, then use list_vms to enumerate VMs, and get_vm_details for in-depth information about a specific VM.",
)


def register(manager: VMRestClientManager) -> None:
    """Register VM tools with the given client manager."""

    def _get_client(host: str):
        """Resolve host alias and return VMRestClient."""
        return manager.get_client(host)

    # ------------------------------------------------------------------
    # Query tools
    # ------------------------------------------------------------------

    @tools.tool()
    def list_vms(host: str) -> str:
        """List all virtual machines registered on a VMware host.

        When to use:
        - Use after list_hosts to see all VMs on a specific host.
        - Use when the user asks to see their VMs, find a VM, or check VM power states.
        - Use to obtain VM IDs (VMX paths) needed by get_vm_details.

        How to use:
        - Pass the host alias (e.g. "workstation-1") or host number (e.g. "1")
          as returned by list_hosts.

        Returns a JSON array of VM objects, each with:
        - ``id``: VMX file path (unique identifier, used as vm_id in other tools).
        - ``path``: full filesystem path to the VMX file.
        - ``power_state``: one of "on", "off", "suspended", or null if unreadable.

        Example output:
        ```json
        [
          {
            "id": "/path/to/vm.vmx",
            "path": "/path/to/vm.vmx",
            "power_state": "on"
          }
        ]
        ```

        Args:
            host: Host alias or host number from list_hosts (e.g. "workstation-1" or "1").
        """
        try:
            client = _get_client(host)
            vms = client.get_vms()
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error communicating with host '{host}': {exc}"

        # Enrich each VM with its power state
        for vm in vms:
            try:
                power = client.get_power_state(vm["id"])
                vm["power_state"] = power
            except VMRestClientError:
                vm["power_state"] = None

        return json.dumps(vms, indent=2)

    @tools.tool()
    def get_vm_details(host: str, vm_id: str) -> str:
        """Get detailed configuration and power state for a specific virtual machine.

        When to use:
        - Use after list_vms to inspect a specific VM's hardware configuration.
        - Use when the user asks about a VM's CPU count, memory, NICs, USB devices,
          VNC settings, guest isolation, or other detailed configuration.
        - Use when the user wants to know the current power state of a specific VM.

        How to use:
        - ``host``: the same host alias or number used in list_vms.
        - ``vm_id``: the VM's ``id`` field (VMX file path) returned by list_vms.

        Returns a JSON object with:
        - ``restrictions``: detailed VM config including ``cpu`` (processor count),
          ``memory`` (MB), ``niclist`` (network adapters with type/vmnet/MAC),
          ``usbList``, ``remoteVNC`` (VNC enabled/port), ``guestIsolation``
          (copy/paste/dnd/hgfs disabled flags), ``cddvdList``, ``serialPortList``,
          ``parallelPortList``, ``firewareType``, and more.
        - ``power_state``: one of "on", "off", "suspended".

        Args:
            host: Host alias or host number from list_hosts (e.g. "workstation-1" or "1").
            vm_id: The VMX file path of the VM, as returned by list_vms (e.g. "/path/to/vm.vmx").
        """
        try:
            client = _get_client(host)
            restrictions = client.get_vm(vm_id)
            power_state = client.get_power_state(vm_id)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        result = {
            "restrictions": restrictions.model_dump(),
            "power_state": power_state,
        }
        return json.dumps(result, indent=2)
