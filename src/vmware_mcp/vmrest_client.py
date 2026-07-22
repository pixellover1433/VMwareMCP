"""HTTP client for a single vmrest.exe instance.

Wraps the VMware Workstation REST API exposed by vmrest.exe.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from vmware_mcp.config import VMRestHostConfig
from vmware_mcp.models import PowerState, Snapshot, VM


class VMRestClientError(Exception):
    """Raised when a vmrest API call fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"[HTTP {status_code}] {message}")


class VMRestClient:
    """REST client for one vmrest.exe server."""

    def __init__(self, config: VMRestHostConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._session.auth = (config.username, config.password)
        self._session.verify = config.verify_ssl
        self._base_url = config.base_url

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a request and return parsed JSON or None on 204."""
        resp = self._session.request(
            method, self._url(path), params=params, json=json, timeout=30
        )
        if resp.status_code == 204:
            return None
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise VMRestClientError(resp.status_code, str(detail))
        return resp.json()

    # ------------------------------------------------------------------
    # VM operations
    # ------------------------------------------------------------------

    def get_vms(self) -> List[VM]:
        """Return all registered VMs."""
        data = self._request("GET", "/api/vms")
        results: List[VM] = []
        for vm_raw in data.get("vms", []) if data else []:
            vm_id = vm_raw.get("id", "")
            results.append(
                VM(
                    id=vm_id,
                    name=vm_raw.get("name", ""),
                    path=vm_raw.get("path", vm_id),
                    power_state=_parse_power_state(vm_raw.get("power_state", "")),
                    guest_os=vm_raw.get("guest_os", ""),
                    cpus=int(vm_raw.get("cpus", 0)),
                    memory_mb=int(vm_raw.get("memory", 0)),
                )
            )
        return results

    def get_vm(self, vm_id: str) -> VM:
        """Return detailed info for a single VM."""
        encoded = quote(vm_id, safe="")
        data = self._request("GET", f"/api/vms/{encoded}")
        if not data:
            raise VMRestClientError(404, f"VM not found: {vm_id}")
        return VM(
            id=data.get("id", vm_id),
            name=data.get("name", ""),
            path=data.get("path", vm_id),
            power_state=_parse_power_state(data.get("power_state", "")),
            guest_os=data.get("guest_os", ""),
            cpus=int(data.get("cpus", 0)),
            memory_mb=int(data.get("memory", 0)),
        )

    def power_operation(self, vm_id: str, op: str) -> None:
        """Perform a power operation on a VM.

        Args:
            vm_id: VMX file path or VM ID.
            op: One of on, off, suspend, shutdown, restart, pause, unpause, reset.
        """
        valid_ops = {
            "on",
            "off",
            "suspend",
            "shutdown",
            "restart",
            "pause",
            "unpause",
            "reset",
        }
        if op not in valid_ops:
            raise ValueError(
                f"Invalid power operation '{op}'. Must be one of: {', '.join(sorted(valid_ops))}"
            )
        encoded = quote(vm_id, safe="")
        self._request("PUT", f"/api/vms/{encoded}/power", params={"op": op})

    # ------------------------------------------------------------------
    # Snapshot operations
    # ------------------------------------------------------------------

    def get_snapshots(self, vm_id: str) -> List[Snapshot]:
        """Return all snapshots for a VM."""
        encoded = quote(vm_id, safe="")
        data = self._request("GET", f"/api/vms/{encoded}/snapshots")
        results: List[Snapshot] = []
        for snap_raw in data.get("snapshots", []) if data else []:
            results.append(
                Snapshot(
                    id=snap_raw.get("id", ""),
                    name=snap_raw.get("name", ""),
                    description=snap_raw.get("description", ""),
                    created=snap_raw.get("created", ""),
                    parent_id=snap_raw.get("parent_id"),
                )
            )
        return results

    def create_snapshot(
        self, vm_id: str, name: str, description: str = ""
    ) -> Snapshot:
        """Create a snapshot for the given VM."""
        encoded = quote(vm_id, safe="")
        data = self._request(
            "POST",
            f"/api/vms/{encoded}/snapshots",
            json={"name": name, "description": description},
        )
        if not data:
            # Some vmrest versions return 204 on success
            return Snapshot(id="", name=name, description=description)
        return Snapshot(
            id=data.get("id", ""),
            name=data.get("name", name),
            description=data.get("description", description),
            created=data.get("created", ""),
            parent_id=data.get("parent_id"),
        )

    def delete_snapshot(self, vm_id: str, snapshot_id: str) -> None:
        """Delete a snapshot by ID."""
        encoded_vm = quote(vm_id, safe="")
        encoded_snap = quote(snapshot_id, safe="")
        self._request("DELETE", f"/api/vms/{encoded_vm}/snapshots/{encoded_snap}")

    def revert_snapshot(self, vm_id: str, snapshot_id: str) -> None:
        """Revert the VM to a given snapshot."""
        encoded_vm = quote(vm_id, safe="")
        encoded_snap = quote(snapshot_id, safe="")
        self._request(
            "PUT", f"/api/vms/{encoded_vm}/snapshots/{encoded_snap}"
        )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _parse_power_state(raw: str) -> PowerState:
    """Map a raw power-state string from the API to the PowerState enum."""
    mapping = {
        "powered on": PowerState.ON,
        "on": PowerState.ON,
        "powered off": PowerState.OFF,
        "off": PowerState.OFF,
        "suspended": PowerState.SUSPENDED,
    }
    return mapping.get(raw.lower().strip(), PowerState.UNKNOWN)
