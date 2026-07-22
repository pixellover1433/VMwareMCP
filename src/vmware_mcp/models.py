"""Pydantic data models for VMware MCP Server."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PowerState(str, Enum):
    """VM power state as reported by vmrest."""

    ON = "on"
    OFF = "off"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class VM(BaseModel):
    """Represents a registered virtual machine."""

    id: str = Field(description="VMX file path used as unique identifier")
    name: str = Field(description="Display name of the VM")
    path: str = Field(description="Full path to the VMX file")
    power_state: PowerState = Field(description="Current power state")
    guest_os: str = Field(default="", description="Guest OS type")
    cpus: int = Field(default=0, description="Number of virtual CPUs")
    memory_mb: int = Field(default=0, description="Allocated memory in MB")


class Snapshot(BaseModel):
    """Represents a VM snapshot."""

    id: str = Field(description="Unique snapshot identifier (UUID)")
    name: str = Field(description="Snapshot name")
    description: str = Field(default="", description="Snapshot description")
    created: str = Field(default="", description="Creation timestamp")
    parent_id: Optional[str] = Field(
        default=None, description="Parent snapshot ID"
    )


class HostInfo(BaseModel):
    """Information about a configured vmrest host."""

    alias: str = Field(description="Friendly host name")
    host: str = Field(description="Hostname or IP address")
    port: int = Field(description="vmrest API port")
    base_url: str = Field(description="Full base URL")
    reachable: bool = Field(description="Whether the host responded to ping")
    index: int = Field(description="1-based host number")


class ListHostsResponse(BaseModel):
    """Response model for list_hosts tool."""

    hosts: list[HostInfo] = Field(description="List of configured vmrest hosts")
    total: int = Field(description="Total number of hosts")
