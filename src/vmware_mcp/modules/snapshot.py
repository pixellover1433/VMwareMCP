"""Snapshot management MCP tools.

Snapshot information is retrieved by invoking the local ``vmcli.exe`` binary
(via :class:`VMCliClient`), since the vmrest REST API does not expose snapshot
queries. The VM ``id`` is first resolved to its VMX filesystem path via the
vmrest API, then passed to vmcli.

These tools only work when the MCP server runs on the same host as VMware
Workstation (vmcli.exe is invoked locally).
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.vmcli_client import VMCliClient, VMCliError
from vmware_mcp.vmrest_client import VMRestClient, VMRestClientError

tools = FastMCP(
    "VMware Snapshots",
    instructions="Use this module to inspect VM snapshots. Use get_vm_snapshots with a VM 'id' (from list_vms) to list all snapshots, see which one is current, and understand their parent/child relationships.",
)

# Module-level client references (set during register)
_client: VMRestClient | None = None
_vmcli: VMCliClient | None = None


def register(client: VMRestClient, vmcli: VMCliClient) -> None:
    """Register snapshot tools with the vmrest and vmcli clients."""
    global _client, _vmcli
    _client = client
    _vmcli = vmcli

    @tools.tool()
    def get_vm_snapshots(vm_id: str) -> str:
        """List all snapshots of a virtual machine.

        When to use:
        - Use when the user asks to see, list, or count a VM's snapshots.
        - Use to find which snapshot is currently active, or to understand the
          snapshot tree (which snapshot descends from which).

        How to use:
        - ``vm_id``: the ``id`` field returned by list_vms. This tool
          automatically resolves the id to the VM's ``.vmx`` file path via the
          vmrest API before querying snapshots — you do NOT need to supply a
          filesystem path.

        This tool runs the local ``vmcli.exe`` binary, so it only works when the
        MCP server runs on the same host as VMware Workstation.

        Returns a JSON object with:
        - ``vm_id``: the VM identifier that was queried.
        - ``vmx_path``: the resolved VMX path used for the vmcli query.
        - ``current_uid``: UID of the currently active snapshot.
        - ``count``: total number of snapshots.
        - ``snapshots``: array of snapshot objects, each with:
          - ``uid``: snapshot unique id within the VM.
          - ``name``: snapshot display name.
          - ``parent_uid``: UID of the parent snapshot (0 = root snapshot).
          - ``is_current``: true if this is the VM's current active snapshot.
        - ``success``: true on success.
        - ``error``: error message on failure, or null on success.

        Example output:
        ```json
        {
          "vm_id": "AB12CD34",
          "vmx_path": "C:\\VMs\\Ubuntu\\Ubuntu.vmx",
          "current_uid": 1,
          "count": 1,
          "snapshots": [
            {
              "uid": 1,
              "name": "Base install",
              "parent_uid": 0,
              "is_current": true
            }
          ],
          "success": true,
          "error": null
        }
        ```

        Args:
            vm_id: The ``id`` field returned by list_vms.
        """
        assert _client is not None
        assert _vmcli is not None

        if not vm_id or not vm_id.strip():
            return json.dumps({
                "vm_id": vm_id,
                "vmx_path": None,
                "current_uid": None,
                "count": 0,
                "snapshots": [],
                "success": False,
                "error": "vm_id is required. Pass the 'id' field from list_vms.",
            }, indent=2)

        # Resolve the VM id to its VMX filesystem path via the vmrest API.
        try:
            vmx_path = _client.get_vm_path(vm_id)
        except VMRestClientError as exc:
            return json.dumps({
                "vm_id": vm_id,
                "vmx_path": None,
                "current_uid": None,
                "count": 0,
                "snapshots": [],
                "success": False,
                "error": f"Could not resolve VM id to a VMX path: {exc}",
            }, indent=2)

        # Query snapshots via the local vmcli.exe binary.
        try:
            result = _vmcli.get_snapshots(vmx_path)
        except VMCliError as exc:
            return json.dumps({
                "vm_id": vm_id,
                "vmx_path": vmx_path,
                "current_uid": None,
                "count": 0,
                "snapshots": [],
                "success": False,
                "error": str(exc),
            }, indent=2)

        payload = {
            "vm_id": vm_id,
            "vmx_path": result.vmx_path,
            "current_uid": result.current_uid,
            "count": result.count,
            "snapshots": [snap.model_dump() for snap in result.snapshots],
            "success": True,
            "error": None,
        }
        return json.dumps(payload, indent=2)
