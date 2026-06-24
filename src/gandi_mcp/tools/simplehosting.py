"""Simple Hosting tools (/v5/simplehosting) — instances + vhosts."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_purchases_allowed, assert_readwrite, get_client


def register_simplehosting_read_tools(mcp: FastMCP) -> None:
    """Register read-only Simple Hosting tools on the server."""

    @mcp.tool(tags={"gandi", "simplehosting"})
    async def gandi_simplehosting_list_instances(ctx: Context) -> list[dict[str, Any]]:
        """List Simple Hosting instances.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).simplehosting_list_instances()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "simplehosting"})
    async def gandi_simplehosting_get_instance(ctx: Context, instance_id: str) -> dict[str, Any]:
        """Get a single Simple Hosting instance by id.

        Args:
            instance_id: Instance UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).simplehosting_get_instance(instance_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "simplehosting"})
    async def gandi_simplehosting_list_vhosts(ctx: Context, instance_id: str) -> list[dict[str, Any]]:
        """List vhosts on a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).simplehosting_list_vhosts(instance_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "simplehosting"})
    async def gandi_simplehosting_get_vhost(ctx: Context, instance_id: str, fqdn: str) -> dict[str, Any]:
        """Get a single vhost on a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.
            fqdn: Vhost fully-qualified domain name.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).simplehosting_get_vhost(instance_id, fqdn)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "simplehosting"})
    async def gandi_simplehosting_get_instance_usage(ctx: Context, instance_id: str) -> dict[str, Any]:
        """Get resource-usage metrics for a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).simplehosting_get_instance_usage(instance_id)
        except Exception as e:
            handle_client_error(e)


def register_simplehosting_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write Simple Hosting tools on the server."""

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_simplehosting_delete_instance(ctx: Context, instance_id: str) -> dict[str, Any]:
        """Delete a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete Simple Hosting instance")
            return await get_client(ctx).simplehosting_delete_instance(instance_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_simplehosting_perform_instance_action(
        ctx: Context, instance_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform an action on a Simple Hosting instance (e.g. restart, console).

        Args:
            instance_id: Instance UUID.
            data: Action payload per the Gandi Simple Hosting schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "perform Simple Hosting instance action")
            return await get_client(ctx).simplehosting_instance_action(instance_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_simplehosting_create_vhost(ctx: Context, instance_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a vhost on a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.
            data: Vhost payload per the Gandi Simple Hosting schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create Simple Hosting vhost")
            return await get_client(ctx).simplehosting_create_vhost(instance_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_simplehosting_delete_vhost(ctx: Context, instance_id: str, fqdn: str) -> dict[str, Any]:
        """Delete a vhost from a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.
            fqdn: Vhost fully-qualified domain name.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete Simple Hosting vhost")
            return await get_client(ctx).simplehosting_delete_vhost(instance_id, fqdn)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_simplehosting_update_vhost(
        ctx: Context, instance_id: str, fqdn: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a vhost on a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.
            fqdn: Vhost fully-qualified domain name.
            data: Partial vhost payload (fields to update).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update Simple Hosting vhost")
            return await get_client(ctx).simplehosting_update_vhost(instance_id, fqdn, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_simplehosting_purge_vhost_cache(ctx: Context, instance_id: str, fqdn: str) -> dict[str, Any]:
        """Purge the cache of a vhost on a Simple Hosting instance.

        Args:
            instance_id: Instance UUID.
            fqdn: Vhost fully-qualified domain name.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "purge Simple Hosting vhost cache")
            return await get_client(ctx).simplehosting_purge_vhost_cache(instance_id, fqdn)
        except Exception as e:
            handle_client_error(e)


def register_simplehosting_purchase_tools(mcp: FastMCP) -> None:
    """Register money-spending Simple Hosting tools on the server.

    DOUBLE-GATED: requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.
    """

    @mcp.tool(
        tags={"gandi", "simplehosting", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_simplehosting_create_instance(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Create a Simple Hosting instance (SPENDS MONEY).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            data: Instance payload (plan, datacenter, etc.) per the Gandi schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create Simple Hosting instance")
            assert_purchases_allowed(ctx, "create Simple Hosting instance")
            return await get_client(ctx).simplehosting_create_instance(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "simplehosting", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_simplehosting_update_instance(
        ctx: Context, instance_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a Simple Hosting instance — plan/size changes may bill (SPENDS MONEY).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            instance_id: Instance UUID.
            data: Partial instance payload (e.g. new plan/size).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update Simple Hosting instance")
            assert_purchases_allowed(ctx, "update Simple Hosting instance")
            return await get_client(ctx).simplehosting_update_instance(instance_id, data)
        except Exception as e:
            handle_client_error(e)


def register_simplehosting_tools(mcp: FastMCP) -> None:
    """Register every Simple Hosting tool (read + write + purchase)."""
    register_simplehosting_read_tools(mcp)
    register_simplehosting_write_tools(mcp)
    register_simplehosting_purchase_tools(mcp)
