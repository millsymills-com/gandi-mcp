"""Linked-zone tools (/v5/linkedzone) — LiveDNS shared/linked zones."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_readwrite, get_client


def register_linkedzone_read_tools(mcp: FastMCP) -> None:
    """Register read-only linked-zone tools on the server."""

    @mcp.tool(title="LinkedZone: List Domains", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_list_domains(ctx: Context) -> list[dict[str, Any]]:
        """List domains that can use linked zones.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_list_domains()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="LinkedZone: Get Domain", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_get_domain(ctx: Context, domain: str) -> dict[str, Any]:
        """Get linked-zone info for a single domain.

        Args:
            domain: Fully-qualified domain name.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_get_domain(domain)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="LinkedZone: List Zones", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_list_zones(ctx: Context) -> list[dict[str, Any]]:
        """List linked zones.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_list_zones()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="LinkedZone: Get Zone", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_get_zone(ctx: Context, zone_id: str) -> dict[str, Any]:
        """Get a single linked zone by id.

        Args:
            zone_id: Linked-zone UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_get_zone(zone_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="LinkedZone: List Tasks", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_list_tasks(ctx: Context) -> list[dict[str, Any]]:
        """List linked-zone background tasks.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_list_tasks()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="LinkedZone: Get Task", tags={"gandi", "linkedzone"})
    async def gandi_linkedzone_get_task(ctx: Context, task_id: str) -> dict[str, Any]:
        """Get a single linked-zone task by id.

        Args:
            task_id: Task UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).linkedzone_get_task(task_id)
        except Exception as e:
            handle_client_error(e)


def register_linkedzone_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write linked-zone tools on the server."""

    @mcp.tool(
        title="LinkedZone: Create Zone",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_linkedzone_create_zone(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Create a linked zone.

        Args:
            data: Zone payload per the Gandi linked-zone schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create linked zone")
            return await get_client(ctx).linkedzone_create_zone(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="LinkedZone: Attach Domain",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_linkedzone_attach_domain(ctx: Context, zone_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Attach a domain to a linked zone.

        Args:
            zone_id: Linked-zone UUID.
            data: Attachment payload (domain to attach) per the Gandi schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "attach domain to linked zone")
            return await get_client(ctx).linkedzone_attach_domain(zone_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="LinkedZone: Update Zone",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_linkedzone_update_zone(ctx: Context, zone_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a linked zone.

        Args:
            zone_id: Linked-zone UUID.
            data: Partial zone payload (fields to update).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update linked zone")
            return await get_client(ctx).linkedzone_update_zone(zone_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="LinkedZone: Delete Zone",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_linkedzone_delete_zone(ctx: Context, zone_id: str) -> dict[str, Any]:
        """Delete a linked zone.

        Args:
            zone_id: Linked-zone UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete linked zone")
            return await get_client(ctx).linkedzone_delete_zone(zone_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="LinkedZone: Link Domains",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_linkedzone_link_domains(ctx: Context, zone_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Link one or more domains to a linked zone.

        Args:
            zone_id: Linked-zone UUID.
            data: Payload listing the domains to link.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "link domains to linked zone")
            return await get_client(ctx).linkedzone_link_domains(zone_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="LinkedZone: Unlink Domains",
        tags={"gandi", "linkedzone", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_linkedzone_unlink_domains(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Unlink one or more domains from their linked zone.

        Args:
            data: Payload listing the domains to unlink.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "unlink domains from linked zone")
            return await get_client(ctx).linkedzone_unlink_domains(data)
        except Exception as e:
            handle_client_error(e)


def register_linkedzone_tools(mcp: FastMCP) -> None:
    """Register every linked-zone tool (read + write)."""
    register_linkedzone_read_tools(mcp)
    register_linkedzone_write_tools(mcp)
