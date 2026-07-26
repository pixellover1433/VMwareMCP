"""Single-host configuration for VMware MCP Server.

Reads VMREST_HOST / VMREST_PORT / … environment variables
and returns a VMRestHostConfig dataclass.

A .env file in the project root is loaded automatically if present.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


# Default install location of vmcli.exe on Windows.
_DEFAULT_VMCLI_PATH = r"C:\Program Files (x86)\VMware\VMware Workstation\vmcli.exe"


@dataclass
class VMRestHostConfig:
    """Connection details for a vmrest.exe instance."""

    host: str
    port: int
    username: str
    password: str
    verify_ssl: bool
    vmcli_path: str = _DEFAULT_VMCLI_PATH

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def load_config() -> VMRestHostConfig:
    """Load the vmrest host configuration from environment variables."""
    host = os.getenv("VMREST_HOST", "")
    if not host:
        raise RuntimeError(
            "VMREST_HOST environment variable is not set. "
            "Please configure it in your .env file or environment."
        )
    return VMRestHostConfig(
        host=host,
        port=int(os.getenv("VMREST_PORT", "8697")),
        username=os.getenv("VMREST_USERNAME", ""),
        password=os.getenv("VMREST_PASSWORD", ""),
        verify_ssl=os.getenv("VMREST_VERIFY_SSL", "false").lower() == "true",
        vmcli_path=os.getenv("VMCLI_PATH", _DEFAULT_VMCLI_PATH),
    )
