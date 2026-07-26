"""Snapshot management MCP tools.

Snapshot information is retrieved by invoking the local ``vmcli.exe`` binary
(via :class:`VMCliClient`), since the vmrest REST API does not expose snapshot
queries. These tools therefore only work when the MCP server runs on the same
host as VMware Workstation.
"""

from __future__ import annotations

import json

from fastmcp import FastMCP

from vmware_mcp.vmcli_client import VMCliClient, VMCliError

tools = FastMCP(
    "VMware Snapshots",
    instructions="Use this module to inspect VM snapshots. Use get_vm_snapshots with a VM's VMX file path (the 'path' field from list_vms) to list all snapshots and see the current snapshot and their parent/child relationships.",
)

# Module-level vmcli client reference (set during register)
_vmcli: VMCliClient | None = None


def register(vmcli: VMCliClient) -> None:
    """Register snapshot tools with the given vmcli client."""
    global _vmcli
    _vmcli = vmcli

    @tools.tool()
    def get_vm_snapshots(vmx_path: str) -> str:
        """List all snapshots of a virtual machine.

        When to use:
        - Use when the user asks to see, list, or count a VM's snapshots.
        - Use to find which snapshot is currently active, or to understand the
          snapshot tree (which snapshot descends from which).

        How to use:
        - ``vmx_path``: the ``path`` field returned by list_vms (the full
          filesystem path to the VM's ``.vmx`` file, e.g.
          ``C:\\VMs\\Ubuntu\\Ubuntu.vmx``). Do NOT pass the ``id`` field.

        This tool runs the local ``vmcli.exe`` binary; it only works when the
        MCP server runs on the same host as VMware Workstation.

        Returns a JSON object with:
        - ``vmx_path``: the queried VMX path.
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
            vmx_path: Full path to the VM's .vmx file (the ``path`` field from list_vms).
        """
        assert _vmcli is not None

        if not vmx_path or not vmx_path.strip():
            return json.dumps({
                "vmx_path": vmx_path,
                "current_uid": None,
                "count": 0,
                "snapshots": [],
                "success": False,
                "error": "vmx_path is required. Pass the 'path' field from list_vms.",
            }, indent=2)

        try:
            result = _vmcli.get_snapshots(vmx_path)
        except VMCliError as exc:
            return json.dumps({
                "vmx_path": vmx_path,
                "current_uid": None,
                "count": 0,
                "snapshots": [],
                "success": False,
                "error": str(exc),
            }, indent=2)

        payload = {
            "vmx_path": result.vmx_path,
            "current_uid": result.current_uid,
            "count": result.count,
            "snapshots": [snap.model_dump() for snap in result.snapshots],
            "success": True,
            "error": None,
        }
        return json.dumps(payload, indent=2)
