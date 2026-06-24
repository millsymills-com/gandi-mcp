"""Mailbox tools (/v5/mailbox) — Gandi's current mailbox product.

This is **distinct from the legacy `email` area** (`/v5/email`, the
``gandi_email_*`` tools). When a user asks about mailboxes, forwards, or slots
on a domain, prefer these ``gandi_mailbox_*`` tools unless the account is
explicitly on the legacy email product.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_purchases_allowed, assert_readwrite, get_client


def register_mailbox_read_tools(mcp: FastMCP) -> None:
    """Register read-only mailbox tools on the server."""

    @mcp.tool(title="Mailbox: List Domains", tags={"gandi", "mailbox"})
    async def gandi_mailbox_list_domains(ctx: Context) -> list[dict[str, Any]]:
        """List domains enabled for the current mailbox product (not legacy email).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_list_domains()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: Get Domain", tags={"gandi", "mailbox"})
    async def gandi_mailbox_get_domain(ctx: Context, domain: str) -> dict[str, Any]:
        """Get mailbox-product configuration for a domain (not legacy email).

        Args:
            domain: Fully-qualified domain name.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_get_domain(domain)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: List Mailboxes", tags={"gandi", "mailbox"})
    async def gandi_mailbox_list_mailboxes(ctx: Context, per_page: int = 100, page: int = 1) -> list[dict[str, Any]]:
        """List mailboxes on the current mailbox product (not legacy email).

        Paginated: returns one page (``per_page``, default 100). If a full page comes back, more may
        exist — page via ``page``/``per_page``. The total count is logged to stderr when Gandi reports it.

        Args:
            per_page: Page size.
            page: Page number.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_list_mailboxes(per_page=per_page, page=page)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: Get Mailbox", tags={"gandi", "mailbox"})
    async def gandi_mailbox_get_mailbox(ctx: Context, email: str) -> dict[str, Any]:
        """Get a single mailbox by address (current mailbox product).

        Args:
            email: Mailbox address.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_get_mailbox(email)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: List Forwards", tags={"gandi", "mailbox"})
    async def gandi_mailbox_list_forwards(ctx: Context, per_page: int = 100, page: int = 1) -> list[dict[str, Any]]:
        """List mailbox forwards (current mailbox product).

        Paginated: returns one page (``per_page``, default 100). If a full page comes back, more may
        exist — page via ``page``/``per_page``. The total count is logged to stderr when Gandi reports it.

        Args:
            per_page: Page size.
            page: Page number.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_list_forwards(per_page=per_page, page=page)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: List Slots", tags={"gandi", "mailbox"})
    async def gandi_mailbox_list_slots(ctx: Context) -> list[dict[str, Any]]:
        """List mailbox slots (purchased capacity for the mailbox product).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_list_slots()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: Get Slot", tags={"gandi", "mailbox"})
    async def gandi_mailbox_get_slot(ctx: Context, slot_id: str) -> dict[str, Any]:
        """Get a single mailbox slot by id.

        Args:
            slot_id: Slot identifier.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_get_slot(slot_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: Get Quotas", tags={"gandi", "mailbox"})
    async def gandi_mailbox_get_quotas(ctx: Context) -> dict[str, Any]:
        """Get mailbox quota usage for the account (current mailbox product).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_get_quotas()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(title="Mailbox: List Products", tags={"gandi", "mailbox"})
    async def gandi_mailbox_list_products(ctx: Context) -> list[dict[str, Any]]:
        """List mailbox products available for purchase (current mailbox product).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).mailbox_list_products()
        except Exception as e:
            handle_client_error(e)


def register_mailbox_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write mailbox tools on the server."""

    @mcp.tool(
        title="Mailbox: Validate Domain",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_mailbox_validate_domain(ctx: Context, domain: str, data: dict[str, Any]) -> dict[str, Any]:
        """Validate a domain's mailbox configuration (current mailbox product).

        Args:
            domain: Fully-qualified domain name.
            data: Validation payload per the Gandi mailbox schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "validate mailbox domain")
            return await get_client(ctx).mailbox_validate_domain(domain, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Update Mailbox",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_mailbox_update_mailbox(ctx: Context, email: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a mailbox (current mailbox product, not legacy email).

        Args:
            email: Mailbox address.
            data: Partial mailbox payload (fields to update).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update mailbox")
            return await get_client(ctx).mailbox_update_mailbox(email, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Delete Mailbox",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_mailbox_delete_mailbox(ctx: Context, email: str) -> dict[str, Any]:
        """Delete a mailbox (current mailbox product, not legacy email).

        Args:
            email: Mailbox address.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete mailbox")
            return await get_client(ctx).mailbox_delete_mailbox(email)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Create Forward",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_mailbox_create_forward(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Create a mailbox forward (current mailbox product).

        Args:
            data: Forward payload (source + destinations) per the Gandi schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create mailbox forward")
            return await get_client(ctx).mailbox_create_forward(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Update Forward",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_mailbox_update_forward(ctx: Context, source: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a mailbox forward by source address (current mailbox product).

        Args:
            source: Source address of the forward.
            data: New forward payload (destinations) per the Gandi schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update mailbox forward")
            return await get_client(ctx).mailbox_update_forward(source, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Delete Forward",
        tags={"gandi", "mailbox", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_mailbox_delete_forward(ctx: Context, source: str) -> dict[str, Any]:
        """Delete a mailbox forward by source address (current mailbox product).

        Args:
            source: Source address of the forward.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete mailbox forward")
            return await get_client(ctx).mailbox_delete_forward(source)
        except Exception as e:
            handle_client_error(e)


def register_mailbox_purchase_tools(mcp: FastMCP) -> None:
    """Register money-spending mailbox tools on the server.

    DOUBLE-GATED: requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.
    """

    @mcp.tool(
        title="Mailbox: Create Mailbox",
        tags={"gandi", "mailbox", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_mailbox_create_mailbox(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Create a mailbox (SPENDS MONEY — current mailbox product, not legacy email).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            data: Mailbox payload (address, slot/product, password) per the Gandi schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create mailbox")
            assert_purchases_allowed(ctx, "create mailbox")
            return await get_client(ctx).mailbox_create_mailbox(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Renew Mailbox",
        tags={"gandi", "mailbox", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_mailbox_renew_mailbox(ctx: Context, email: str, data: dict[str, Any]) -> dict[str, Any]:
        """Renew a mailbox (SPENDS MONEY — current mailbox product, not legacy email).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            email: Mailbox address.
            data: Renewal payload. `duration` is the renewal duration in months (Gandi accepts 1 or 12).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "renew mailbox")
            assert_purchases_allowed(ctx, "renew mailbox")
            return await get_client(ctx).mailbox_renew_mailbox(email, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        title="Mailbox: Buy Product",
        tags={"gandi", "mailbox", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_mailbox_buy_product(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Buy a mailbox product / slot (SPENDS MONEY — current mailbox product).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            data: Product purchase payload per the Gandi mailbox schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "buy mailbox product")
            assert_purchases_allowed(ctx, "buy mailbox product")
            return await get_client(ctx).mailbox_buy_product(data)
        except Exception as e:
            handle_client_error(e)


def register_mailbox_tools(mcp: FastMCP) -> None:
    """Register every mailbox tool (read + write + purchase)."""
    register_mailbox_read_tools(mcp)
    register_mailbox_write_tools(mcp)
    register_mailbox_purchase_tools(mcp)
