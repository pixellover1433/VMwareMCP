"""Pydantic data models for VMware MCP Server."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# VM configuration (from GET /api/vms/{id}/restrictions)
# ------------------------------------------------------------------


class VMCPU(BaseModel):
    """CPU configuration for a VM."""

    processors: int = Field(default=1, description="Number of virtual processors")


class VMConfig(BaseModel):
    """VM configuration returned by GET /api/vms/{id}/restrictions.

    Only includes fields that are relevant for the MCP tools.
    """

    id: str = Field(default="", description="VM identifier (VMX path)")
    cpu: VMCPU = Field(default_factory=VMCPU, description="CPU configuration")
    memory: int = Field(default=0, description="Allocated memory in MB")


# ------------------------------------------------------------------
# Snapshot (from `vmcli snapshot <vmx> query --format json`)
# ------------------------------------------------------------------


class Snapshot(BaseModel):
    """Represents a single VM snapshot as reported by vmcli."""

    uid: int = Field(description="Snapshot unique identifier within the VM")
    name: str = Field(description="Snapshot display name")
    parent_uid: int = Field(
        default=0,
        description="UID of the parent snapshot, or 0 if this is a root snapshot",
    )
    is_current: bool = Field(
        default=False,
        description="True if this snapshot is the VM's current active state",
    )


class SnapshotQueryResult(BaseModel):
    """Parsed result of a vmcli snapshot query for one VM."""

    vmx_path: str = Field(description="Filesystem path to the VMX file queried")
    current_uid: int = Field(
        default=0, description="UID of the current active snapshot"
    )
    count: int = Field(default=0, description="Total number of snapshots")
    snapshots: list[Snapshot] = Field(
        default_factory=list, description="Flat list of snapshots"
    )
