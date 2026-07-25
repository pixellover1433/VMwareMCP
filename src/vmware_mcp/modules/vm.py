"""VM management MCP tools.

Tools for listing and inspecting virtual machines.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.vmrest_client import VMRestClient, VMRestClientError

tools = FastMCP(
    "VMware VMs",
    instructions="Use this module to list virtual machines and inspect their configuration. Use list_vms to enumerate VMs, and get_vm_details for in-depth information about a specific VM.",
)

# Module-level client reference (set during register)
_client: VMRestClient | None = None


def register(client: VMRestClient) -> None:
    """Register VM tools with the given client."""
    global _client
    _client = client

    @tools.tool()
    def list_vms() -> str:
        """List all virtual machines registered on the VMware host.

        When to use:
        - Use when the user asks to see their VMs, find a VM, or check VM power states.
        - Use to obtain VM IDs (VMX paths) needed by get_vm_details.

        Returns a JSON array of VM objects, each with:
        - ``id``: VMX file path (unique identifier, used as vm_id in other tools).
        - ``path``: full filesystem path to the VMX file.
        - ``name``: human-readable VM display name (from the VMX config).
        - ``power_state``: one of "on", "off", "suspended", or null if unreadable.

        Example output:
        ```json
        [
          {
            "id": "/path/to/vm.vmx",
            "path": "/path/to/vm.vmx",
            "name": "My Virtual Machine",
            "power_state": "on"
          }
        ]
        ```

        No arguments required.
        """
        assert _client is not None
        try:
            vms = _client.get_vms()
        except VMRestClientError as exc:
            return f"Error communicating with vmrest: {exc}"

        # Enrich each VM with its power state
        for vm in vms:
            try:
                power = _client.get_power_state(vm["id"])
                vm["power_state"] = power
            except VMRestClientError:
                vm["power_state"] = None

        return json.dumps(vms, indent=2)

    @tools.tool()
    def get_vm_details(vm_id: str) -> str:
        """Get detailed configuration and power state for a specific virtual machine.

        When to use:
        - Use after list_vms to inspect a specific VM's hardware configuration.
        - Use when the user asks about a VM's CPU count, memory, NICs, USB devices,
          VNC settings, guest isolation, or other detailed configuration.
        - Use when the user wants to know the current power state of a specific VM.

        How to use:
        - ``vm_id``: the VM's ``id`` field (VMX file path) returned by list_vms.

        Returns a JSON object with:
        - ``name``: human-readable VM display name.
        - ``restrictions``: detailed VM config including ``cpu`` (processor count),
          ``memory`` (MB), ``niclist`` (network adapters with type/vmnet/MAC),
          ``usbList``, ``remoteVNC`` (VNC enabled/port), ``guestIsolation``
          (copy/paste/dnd/hgfs disabled flags), ``cddvdList``, ``serialPortList``,
          ``parallelPortList``, ``firewareType``, and more.
        - ``power_state``: one of "on", "off", "suspended".

        Args:
            vm_id: The VMX file path of the VM, as returned by list_vms (e.g. "/path/to/vm.vmx").
        """
        assert _client is not None
        try:
            name = _client.get_vm_param(vm_id, "displayName") or ""
            restrictions = _client.get_vm(vm_id)
            power_state = _client.get_power_state(vm_id)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        result = {
            "name": name,
            "restrictions": restrictions.model_dump(),
            "power_state": power_state,
        }
        return json.dumps(result, indent=2)
