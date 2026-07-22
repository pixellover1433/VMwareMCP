"""VM management MCP tools.

Tools for listing, inspecting, and controlling virtual machines.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.client_manager import HostNotFoundError, VMRestClientManager
from vmware_mcp.vmrest_client import VMRestClientError

tools = FastMCP("VMware VMs")


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

        Returns JSON with each VM's ``id``, ``path``, and ``power_state``.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
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
        """Get detailed restrictions/config and power state for a specific VM.

        Returns a JSON object containing:
        - ``restrictions``: data from ``GET /api/vms/{id}/restrictions``
          (CPU, memory, NICs, USB, VNC, isolation settings, etc.)
        - ``power_state``: data from ``GET /api/vms/{id}/power``

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
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

    # ------------------------------------------------------------------
    # Power tools
    # ------------------------------------------------------------------

    def _power_op(host: str, vm_id: str, op: str, op_label: str) -> str:
        """Execute a power operation and return a result message."""
        try:
            client = _get_client(host)
            client.power_operation(vm_id, op)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"
        return f"VM '{vm_id}' {op_label} successfully on host '{host}'."

    @tools.tool()
    def power_on_vm(host: str, vm_id: str) -> str:
        """Power on (start) a virtual machine.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        return _power_op(host, vm_id, "on", "powered on")

    @tools.tool()
    def power_off_vm(host: str, vm_id: str) -> str:
        """Hard power off a virtual machine (equivalent to pulling the plug).

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        return _power_op(host, vm_id, "off", "powered off")

    @tools.tool()
    def suspend_vm(host: str, vm_id: str) -> str:
        """Suspend a running virtual machine (save state to disk).

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        return _power_op(host, vm_id, "suspend", "suspended")

    @tools.tool()
    def shutdown_vm(host: str, vm_id: str) -> str:
        """Gracefully shut down a virtual machine via VMware Tools.

        Requires VMware Tools to be installed and running inside the guest OS.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        return _power_op(host, vm_id, "shutdown", "shut down")

    @tools.tool()
    def restart_vm(host: str, vm_id: str) -> str:
        """Gracefully restart a virtual machine via VMware Tools.

        Requires VMware Tools to be installed and running inside the guest OS.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        return _power_op(host, vm_id, "restart", "restarted")
