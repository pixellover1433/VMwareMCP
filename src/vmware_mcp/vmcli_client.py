"""Local client for VMware Workstation's ``vmcli.exe``.

Some operations (such as querying snapshots) are not exposed by the vmrest
REST API and must be performed by invoking ``vmcli.exe`` directly on the host
where VMware Workstation is installed. This module wraps those subprocess
calls and parses their JSON output into typed models.

Note: This client only works when the MCP server runs on the same machine as
VMware Workstation (it shells out to the local ``vmcli.exe`` binary).
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

from vmware_mcp.config import VMRestHostConfig
from vmware_mcp.models import Snapshot, SnapshotQueryResult

logger = logging.getLogger("vmware_mcp.vmcli")


class VMCliError(Exception):
    """Raised when a vmcli.exe invocation fails."""

    def __init__(self, message: str, *, returncode: int | None = None):
        self.returncode = returncode
        super().__init__(message)


class VMCliClient:
    """Wrapper around the local ``vmcli.exe`` binary."""

    #: Maximum seconds to wait for a vmcli invocation before giving up.
    _TIMEOUT_SECONDS = 60

    def __init__(self, config: VMRestHostConfig) -> None:
        self.config = config
        self._vmcli_path = config.vmcli_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: list[str]) -> str:
        """Run vmcli with the given args and return stdout as text.

        Raises VMCliError on missing binary, non-zero exit, or timeout.
        """
        if not Path(self._vmcli_path).is_file():
            raise VMCliError(
                f"vmcli.exe not found at '{self._vmcli_path}'. "
                "Set the VMCLI_PATH environment variable to the correct path. "
                "This tool requires the MCP server to run on the same host as "
                "VMware Workstation."
            )

        cmd = [self._vmcli_path, *args]
        logger.info("Running vmcli: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise VMCliError(
                f"vmcli command timed out after {self._TIMEOUT_SECONDS}s."
            ) from exc
        except OSError as exc:
            raise VMCliError(f"Failed to launch vmcli.exe: {exc}") from exc

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise VMCliError(
                f"vmcli exited with code {proc.returncode}: {detail}",
                returncode=proc.returncode,
            )
        return proc.stdout

    # ------------------------------------------------------------------
    # Snapshot operations
    # ------------------------------------------------------------------

    def get_snapshots(self, vmx_path: str) -> SnapshotQueryResult:
        """Query all snapshots for the VM at ``vmx_path``.

        Runs ``vmcli snapshot <vmx_path> query --format json`` and parses the
        result. The raw vmcli output looks like::

            {
              "currentUID": 1,
              "helperUID": 0,
              "snapshots": [
                {"displayName": "snap1", "parentUID": 0, "uid": 1}
              ]
            }

        Args:
            vmx_path: Full filesystem path to the ``.vmx`` file (the ``path``
                field returned by ``list_vms``).

        Returns:
            A :class:`SnapshotQueryResult` with the parsed snapshot list.
        """
        stdout = self._run(["snapshot", vmx_path, "query", "--format", "json"])

        try:
            raw: Dict[str, Any] = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise VMCliError(
                f"Could not parse vmcli JSON output: {exc}. Raw output: {stdout[:500]}"
            ) from exc

        raw_snapshots = raw.get("snapshots") or []
        snapshots: list[Snapshot] = []
        current_uid = int(raw.get("currentUID", 0) or 0)
        for item in raw_snapshots:
            uid = int(item.get("uid", 0) or 0)
            snapshots.append(
                Snapshot(
                    uid=uid,
                    name=item.get("displayName", ""),
                    parent_uid=int(item.get("parentUID", 0) or 0),
                    is_current=(uid == current_uid),
                )
            )

        return SnapshotQueryResult(
            vmx_path=vmx_path,
            current_uid=current_uid,
            count=len(snapshots),
            snapshots=snapshots,
        )
