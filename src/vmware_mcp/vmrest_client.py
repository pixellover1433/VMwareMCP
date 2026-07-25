"""HTTP client for a single vmrest.exe instance.

Wraps the VMware Workstation REST API exposed by vmrest.exe.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from vmware_mcp.config import VMRestHostConfig
from vmware_mcp.models import Snapshot, VMConfig


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

    def get_vm_param(self, vm_id: str, param_name: str) -> Optional[str]:
        """Return a single VM configuration parameter value.

        Calls ``GET /api/vms/{id}/params/{name}``.

        The vmrest API returns ``{"name": "<param_name>", "value": "<value>"}``.
        Returns the value string, or ``None`` if the parameter is not found.
        """
        encoded = quote(vm_id, safe="")
        try:
            data = self._request("GET", f"/api/vms/{encoded}/params/{param_name}")
        except VMRestClientError as exc:
            if exc.status_code == 404:
                return None
            raise
        if not data:
            return None
        return data.get("value")

    def get_vms(self) -> List[Dict[str, str]]:
        """Return all registered VMs with their display names.

        First calls ``GET /api/vms`` to get the list of VMs, then calls
        ``GET /api/vms/{id}/params/displayName`` for each VM to retrieve
        its human-readable name.

        Returns a list of dicts with ``id``, ``path``, and ``name`` keys::

            [{"id": "<vmx-path>", "path": "<vmx-path>", "name": "My VM"}, ...]
        """
        data = self._request("GET", "/api/vms")
        # vmrest returns a list directly, not a dict wrapper
        vm_list: list = data if isinstance(data, list) else data.get("vms", []) if data else []
        results: List[Dict[str, str]] = []
        for vm_raw in vm_list:
            vm_id = vm_raw.get("id", "")
            name = self.get_vm_param(vm_id, "displayName") or ""
            results.append({
                "id": vm_id,
                "path": vm_raw.get("path", ""),
                "name": name,
            })
        return results

    def get_power_state(self, vm_id: str) -> Dict[str, Any]:
        """Return power state for a single VM.

        Calls ``GET /api/vms/{id}/power``.
        """
        encoded = quote(vm_id, safe="")
        data = self._request("GET", f"/api/vms/{encoded}/power")
        if not data:
            raise VMRestClientError(404, f"VM not found: {vm_id}")
        return data

    def get_vm(self, vm_id: str) -> VMConfig:
        """Return detailed configuration for a single VM.

        Calls ``GET /api/vms/{id}/restrictions`` and maps the response to a
        :class:`VMConfig` model containing only ``id``, ``cpu``, and ``memory``.
        """
        encoded = quote(vm_id, safe="")
        data = self._request("GET", f"/api/vms/{encoded}/restrictions")
        if not data:
            raise VMRestClientError(404, f"VM not found: {vm_id}")
        return VMConfig.model_validate(data)

    def get_vm_nic_ips(self, vm_id: str) -> Optional[Dict[str, Any]]:
        """Return NIC IP information for a VM.

        Calls ``GET /api/vms/{id}/nicips``.

        Returns the raw JSON response containing ``nics``, ``routes``, and
        ``dns`` objects, or ``None`` if the endpoint is not available.
        """
        encoded = quote(vm_id, safe="")
        try:
            return self._request("GET", f"/api/vms/{encoded}/nicips")
        except VMRestClientError as exc:
            if exc.status_code == 404:
                return None
            raise

    def power_operation(self, vm_id: str, op: str) -> Dict[str, Any]:
        """Perform a power operation on a VM.

        Calls ``PUT /api/vms/{id}/power`` with a JSON body containing
        ``{"operation": "<op>"}``.

        Args:
            vm_id: The VM identifier returned by ``list_vms``.
            op: One of on, off, shutdown, suspend, pause, unpause.

        Returns:
            The JSON response from vmrest, typically
            ``{"power_state": "<new_state>"}``.
        """
        valid_ops = {
            "on",
            "off",
            "shutdown",
            "suspend",
            "pause",
            "unpause",
        }
        if op not in valid_ops:
            raise ValueError(
                f"Invalid power operation '{op}'. Must be one of: {', '.join(sorted(valid_ops))}"
            )
        encoded = quote(vm_id, safe="")
        data = self._request(
            "PUT", f"/api/vms/{encoded}/power", json={"operation": op}
        )
        return data if data else {}

    # ------------------------------------------------------------------
    # Snapshot operations
    # ------------------------------------------------------------------

    def get_snapshots(self, vm_id: str) -> List[Snapshot]:
        """Return all snapshots for a VM."""
        encoded = quote(vm_id, safe="")
        data = self._request("GET", f"/api/vms/{encoded}/snapshots")
        results: List[Snapshot] = []
        # vmrest may return a list directly or wrapped in a dict
        snap_list = data if isinstance(data, list) else data.get("snapshots", []) if data else []
        for snap_raw in snap_list:
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
