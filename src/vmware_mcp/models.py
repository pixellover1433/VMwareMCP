"""Pydantic data models for VMware MCP Server."""

from __future__ import annotations

from typing import Optional

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
# Snapshot (from GET /api/vms/{id}/snapshots)
# ------------------------------------------------------------------


class Snapshot(BaseModel):
    """Represents a VM snapshot."""

    id: str = Field(description="Unique snapshot identifier (UUID)")
    name: str = Field(description="Snapshot name")
    description: str = Field(default="", description="Snapshot description")
    created: str = Field(default="", description="Creation timestamp")
    parent_id: Optional[str] = Field(
        default=None, description="Parent snapshot ID"
    )
