"""Multi-host client manager.

Maintains a pool of VMRestClient instances keyed by alias (and index)
so that MCP tools can target any configured vmrest host.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from vmware_mcp.config import VMRestHostConfig, load_hosts
from vmware_mcp.models import HostInfo
from vmware_mcp.vmrest_client import VMRestClient, VMRestClientError

logger = logging.getLogger(__name__)


class HostNotFoundError(Exception):
    """Raised when a requested host alias is not configured."""

    def __init__(self, host: str, available: List[str]):
        self.host = host
        self.available = available
        super().__init__(
            f"Host '{host}' not found. Available hosts: {', '.join(available)}"
        )


class VMRestClientManager:
    """Manages VMRestClient instances for all configured hosts."""

    def __init__(self, configs: List[VMRestHostConfig] | None = None) -> None:
        if configs is None:
            configs = load_hosts()
        self._configs: List[VMRestHostConfig] = configs
        # alias -> VMRestClient
        self._clients: Dict[str, VMRestClient] = {}
        # index (as string) -> alias for number-based lookup
        self._index_to_alias: Dict[str, str] = {}

        for cfg in configs:
            client = VMRestClient(cfg)
            self._clients[cfg.alias] = client
            self._index_to_alias[str(cfg.index)] = cfg.alias
            logger.info("Registered vmrest host: %s (%s:%d)", cfg.alias, cfg.host, cfg.port)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_client(self, host: str) -> VMRestClient:
        """Return a VMRestClient for the given alias or host number.

        Lookup order:
        1. Exact alias match
        2. Host number (e.g. "1" -> alias "host-1")
        """
        if host in self._clients:
            return self._clients[host]

        alias = self._index_to_alias.get(host)
        if alias and alias in self._clients:
            return self._clients[alias]

        available = list(self._clients.keys())
        raise HostNotFoundError(host, available)

    @property
    def aliases(self) -> List[str]:
        """Return list of all registered host aliases."""
        return list(self._clients.keys())

    # ------------------------------------------------------------------
    # Host info / health
    # ------------------------------------------------------------------

    def list_hosts(self) -> List[HostInfo]:
        """Return connection info for every configured host."""
        results: List[HostInfo] = []
        for cfg in self._configs:
            reachable = self._check_connectivity(cfg)
            results.append(
                HostInfo(
                    alias=cfg.alias,
                    host=cfg.host,
                    port=cfg.port,
                    base_url=cfg.base_url,
                    reachable=reachable,
                    index=cfg.index,
                )
            )
        return results

    def _check_connectivity(self, cfg: VMRestHostConfig) -> bool:
        """Quick health-check: GET /api/vms with a short timeout."""
        try:
            client = self._clients.get(cfg.alias)
            if client is None:
                return False
            client._request("GET", "/api/vms")
            return True
        except (VMRestClientError, Exception) as exc:
            logger.debug("Connectivity check failed for %s: %s", cfg.alias, exc)
            return False

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close_all(self) -> None:
        """Close all HTTP sessions."""
        for client in self._clients.values():
            client.close()
