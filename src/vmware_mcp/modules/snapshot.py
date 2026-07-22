"""Snapshot management MCP tools.

Tools for listing, creating, deleting, and reverting VM snapshots.
"""

from __future__ import annotations

from fastmcp import FastMCP

from vmware_mcp.client_manager import HostNotFoundError, VMRestClientManager
from vmware_mcp.vmrest_client import VMRestClientError

tools = FastMCP("VMware Snapshots")


def register(manager: VMRestClientManager) -> None:
    """Register snapshot tools with the given client manager."""

    def _get_client(host: str):
        """Resolve host alias and return VMRestClient."""
        return manager.get_client(host)

    @tools.tool()
    def list_snapshots(host: str, vm_id: str) -> str:
        """List all snapshots for a virtual machine.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
        """
        try:
            client = _get_client(host)
            snapshots = client.get_snapshots(vm_id)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        if not snapshots:
            return f"No snapshots found for VM '{vm_id}' on host '{host}'."

        lines = [f"Snapshots for VM '{vm_id}' on host '{host}':", ""]
        lines.append(f"{'Name':<30} {'ID':<38} {'Created'}")
        lines.append("-" * 90)
        for snap in snapshots:
            created = snap.created or "N/A"
            lines.append(f"{snap.name:<30} {snap.id:<38} {created}")

        lines.append("")
        lines.append(f"Total: {len(snapshots)} snapshot(s)")
        return "\n".join(lines)

    @tools.tool()
    def create_snapshot(
        host: str, vm_id: str, name: str, description: str = ""
    ) -> str:
        """Create a new snapshot of a virtual machine.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
            name: Name for the new snapshot.
            description: Optional description for the snapshot.
        """
        try:
            client = _get_client(host)
            snap = client.create_snapshot(vm_id, name, description)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        desc = f" (description: {description})" if description else ""
        return f"Snapshot '{snap.name}' created successfully for VM '{vm_id}' on host '{host}'.{desc}"

    @tools.tool()
    def delete_snapshot(host: str, vm_id: str, snapshot_id: str) -> str:
        """Delete a snapshot from a virtual machine.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
            snapshot_id: The UUID of the snapshot to delete.
        """
        try:
            client = _get_client(host)
            client.delete_snapshot(vm_id, snapshot_id)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        return f"Snapshot '{snapshot_id}' deleted successfully from VM '{vm_id}' on host '{host}'."

    @tools.tool()
    def revert_to_snapshot(host: str, vm_id: str, snapshot_id: str) -> str:
        """Revert a virtual machine to a specific snapshot.

        This will restore the VM's state to the point when the snapshot was taken.

        Args:
            host: Host alias or number (e.g. "my-workstation" or "1").
            vm_id: The VMX file path of the VM.
            snapshot_id: The UUID of the snapshot to revert to.
        """
        try:
            client = _get_client(host)
            client.revert_snapshot(vm_id, snapshot_id)
        except HostNotFoundError as exc:
            return str(exc)
        except VMRestClientError as exc:
            return f"Error: {exc}"

        return f"VM '{vm_id}' reverted to snapshot '{snapshot_id}' on host '{host}'."
