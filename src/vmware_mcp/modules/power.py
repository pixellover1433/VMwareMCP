"""Power management MCP tools.

Tools for querying and controlling VM power state.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.vmrest_client import VMRestClient, VMRestClientError

tools = FastMCP(
    "VMware Power",
    instructions="Use this module to query and control the power state of virtual machines. Use get_vm_power_state to check a VM's current state, and set_vm_power_state to power on, off, suspend, reset, or perform other power operations.",
)

# Module-level client reference (set during register)
_client: VMRestClient | None = None


def register(client: VMRestClient) -> None:
    """Register power tools with the given client."""
    global _client
    _client = client

    @tools.tool()
    def get_vm_power_state(vm_id: str) -> str:
        """Get the current power state of a virtual machine.

        When to use:
        - Use when the user asks whether a VM is running, stopped, or suspended.
        - Use before performing a power operation to verify the current state.

        Returns a JSON object with:
        - ``vm_id``: the VM identifier.
        - ``power_state``: one of "on", "off", "suspended".

        Args:
            vm_id: The ``id`` field returned by list_vms.
        """
        assert _client is not None
        try:
            power_state = _client.get_power_state(vm_id)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        result = {
            "vm_id": vm_id,
            "power_state": power_state,
        }
        return json.dumps(result, indent=2)

    @tools.tool()
    def set_vm_power_state(vm_id: str, operation: str) -> str:
        """Perform a power operation on a virtual machine.

        When to use:
        - Use when the user wants to start, stop, suspend, pause, or otherwise control a VM.
        - Use after confirming the current power state with get_vm_power_state.

        Args:
            vm_id: The ``id`` field returned by list_vms.
            operation: The power operation to perform. Must be one of:
                - ``on``: Power on the VM.
                - ``off``: Power off the VM (hard power off).
                - ``shutdown``: Gracefully shut down the guest OS.
                - ``suspend``: Suspend the VM.
                - ``pause``: Pause the VM.
                - ``unpause``: Unpause the VM.

        Returns a JSON object with:
        - ``vm_id``: the VM identifier.
        - ``operation``: the operation that was performed.
        - ``power_state``: the resulting power state reported by vmrest (e.g. "pausing", "on", "off").
        - ``success``: true if the operation completed successfully.
        - ``error``: error message if the operation failed, or null on success.
        """
        assert _client is not None
        try:
            resp = _client.power_operation(vm_id, operation)
        except VMRestClientError as exc:
            return json.dumps({
                "vm_id": vm_id,
                "operation": operation,
                "power_state": None,
                "success": False,
                "error": str(exc),
            }, indent=2)
        except ValueError as exc:
            return json.dumps({
                "vm_id": vm_id,
                "operation": operation,
                "power_state": None,
                "success": False,
                "error": str(exc),
            }, indent=2)

        result = {
            "vm_id": vm_id,
            "operation": operation,
            "power_state": resp.get("power_state"),
            "success": True,
            "error": None,
        }
        return json.dumps(result, indent=2)
