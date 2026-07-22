"""Snapshot management MCP tools.

This module previously contained snapshot tools. All snapshot tools have been
removed. The module is retained as a placeholder for potential future use.
"""

from __future__ import annotations

from fastmcp import FastMCP

tools = FastMCP(
    "VMware Snapshots",
    instructions="No snapshot tools are currently available.",
)


def register(manager) -> None:
    """Register snapshot tools (currently none)."""
