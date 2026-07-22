"""Multi-host configuration for VMware MCP Server.

Reads VMREST_HOST_N / VMREST_PORT_N / ... environment variables
and returns a list of VMRestHostConfig dataclasses.

A .env file in the project root is loaded automatically if present.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


@dataclass
class VMRestHostConfig:
    """Connection details for a single vmrest.exe instance."""

    host: str
    port: int
    username: str
    password: str
    verify_ssl: bool
    alias: str
    index: int  # 1-based host number

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"


def load_hosts() -> List[VMRestHostConfig]:
    """Scan VMREST_HOST_N env vars sequentially and return host configs.

    The scan starts at N=1 and stops when VMREST_HOST_N is not set.
    """
    hosts: List[VMRestHostConfig] = []
    n = 1
    while True:
        host = os.getenv(f"VMREST_HOST_{n}")
        if not host:
            break
        hosts.append(
            VMRestHostConfig(
                host=host,
                port=int(os.getenv(f"VMREST_PORT_{n}", "8697")),
                username=os.getenv(f"VMREST_USERNAME_{n}", ""),
                password=os.getenv(f"VMREST_PASSWORD_{n}", ""),
                verify_ssl=os.getenv(f"VMREST_VERIFY_SSL_{n}", "false").lower()
                == "true",
                alias=os.getenv(f"VMREST_ALIAS_{n}", f"host-{n}"),
                index=n,
            )
        )
        n += 1
    return hosts
