"""Pydantic data models for VMware MCP Server."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, Field


class PowerState(str, Enum):
    """VM power state as reported by vmrest."""

    ON = "on"
    OFF = "off"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


# ------------------------------------------------------------------
# VM list item (from GET /api/vms)
# ------------------------------------------------------------------


class VM(BaseModel):
    """Represents a registered virtual machine."""

    id: str = Field(description="VMX file path used as unique identifier")
    name: str = Field(description="Display name of the VM")
    path: str = Field(description="Full path to the VMX file")
    power_state: PowerState = Field(description="Current power state")
    guest_os: str = Field(default="", description="Guest OS type")
    cpus: int = Field(default=0, description="Number of virtual CPUs")
    memory_mb: int = Field(default=0, description="Allocated memory in MB")


# ------------------------------------------------------------------
# VM restrictions detail (from GET /api/vms/{id}/restrictions)
# ------------------------------------------------------------------


class VMCPU(BaseModel):
    """CPU configuration for a VM."""

    processors: int = Field(default=1, description="Number of virtual processors")


def _int_or_zero(v: Union[str, int, None]) -> int:
    """Coerce empty strings / None to 0, otherwise parse as int."""
    if v is None or v == "":
        return 0
    return int(v)


class ApplianceView(BaseModel):
    """Appliance view metadata."""

    author: str = Field(default="")
    version: str = Field(default="")
    port: Annotated[int, BeforeValidator(_int_or_zero)] = Field(default=0)
    showAtPowerOn: str = Field(default="false")


class DeviceItem(BaseModel):
    """Generic device entry (CD/DVD, floppy, parallel, serial)."""

    index: int = Field(default=0)
    startConnected: Union[str, bool] = Field(default=False)
    connectionStatus: int = Field(default=0)
    devicePath: str = Field(default="")


class DeviceList(BaseModel):
    """A numbered list of generic devices."""

    num: int = Field(default=0)
    devices: List[DeviceItem] = Field(default_factory=list)


class GuestIsolation(BaseModel):
    """Guest isolation settings."""

    copyDisabled: Union[str, bool] = Field(default=False)
    dndDisabled: Union[str, bool] = Field(default=False)
    hgfsDisabled: Union[str, bool] = Field(default=False)
    pasteDisabled: Union[str, bool] = Field(default=False)


class NIC(BaseModel):
    """Network interface card entry."""

    index: int = Field(default=0)
    type: str = Field(default="")
    vmnet: str = Field(default="")
    macAddress: str = Field(default="")


class NICList(BaseModel):
    """A numbered list of NICs."""

    num: int = Field(default=0)
    nics: List[NIC] = Field(default_factory=list)


class USBDevice(BaseModel):
    """USB device entry."""

    index: int = Field(default=0)
    connected: Union[str, bool] = Field(default=False)
    backingInfo: str = Field(default="")
    BackingType: int = Field(default=0)


class USBList(BaseModel):
    """A numbered list of USB devices."""

    num: int = Field(default=0)
    usbDevices: List[USBDevice] = Field(default_factory=list)


class RemoteVNC(BaseModel):
    """Remote VNC configuration."""

    VNCEnabled: Union[str, bool] = Field(default=False)
    VNCPort: int = Field(default=0)


class VMRestrictions(BaseModel):
    """Detailed VM configuration returned by GET /api/vms/{id}/restrictions."""

    id: str = Field(default="")
    managedOrg: str = Field(default="")
    integrityconstraint: str = Field(default="false")
    cpu: VMCPU = Field(default_factory=VMCPU)
    memory: int = Field(default=0, description="Memory in MB")
    applianceView: ApplianceView = Field(default_factory=ApplianceView)
    cddvdList: DeviceList = Field(default_factory=DeviceList)
    floopyList: DeviceList = Field(default_factory=DeviceList)
    firewareType: int = Field(default=0)
    guestIsolation: GuestIsolation = Field(default_factory=GuestIsolation)
    niclist: NICList = Field(default_factory=NICList)
    parallelPortList: DeviceList = Field(default_factory=DeviceList)
    serialPortList: DeviceList = Field(default_factory=DeviceList)
    usbList: USBList = Field(default_factory=USBList)
    remoteVNC: RemoteVNC = Field(default_factory=RemoteVNC)


class Snapshot(BaseModel):
    """Represents a VM snapshot."""

    id: str = Field(description="Unique snapshot identifier (UUID)")
    name: str = Field(description="Snapshot name")
    description: str = Field(default="", description="Snapshot description")
    created: str = Field(default="", description="Creation timestamp")
    parent_id: Optional[str] = Field(
        default=None, description="Parent snapshot ID"
    )
