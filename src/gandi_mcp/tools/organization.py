"""Organization tools (/v5/organization)."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_readwrite, get_client


def register_organization_read_tools(mcp: FastMCP) -> None:
    """Register read-only organization tools on the server."""

    @mcp.tool(tags={"gandi", "organization"})
    async def gandi_org_get_user_info(ctx: Context) -> dict[str, Any]:
        """Profile info for the token owner (name, email, lang, scope).

        Args:
            ctx: FastMCP request context.

        Returns:
            Gandi API response payload.
        """
        try:
            return await get_client(ctx).get_user_info()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "organization"})
    async def gandi_org_list_organizations(
        ctx: Context,
        name: str | None = None,
        permission: str | None = None,
        org_type: str | None = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """List organizations the token can access.

        Paginated: returns one page (``per_page``, default 100). If a full page comes back, more may
        exist — page via ``page``/``per_page``. The total count is logged to stderr when Gandi reports it.

        Returns: Gandi organization list — see `https://api.gandi.net/docs`.

        Args:
            name: Filter on organization name (substring match).
            permission: Filter by granted permission ("view", "admin", "billing").
            org_type: Filter by org type ("individual", "company", "association",
                "publicbody").
            per_page: Page size.
            page: Page number.
        """
        try:
            return await get_client(ctx).list_organizations(
                name=name, permission=permission, type=org_type, per_page=per_page, page=page
            )
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "organization"})
    async def gandi_org_get_organization(ctx: Context, org_id: str) -> dict[str, Any]:
        """Retrieve one organization by UUID.

        Args:
            org_id: Organization UUID (aka sharing_id).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).get_organization(org_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "organization"})
    async def gandi_org_list_customers(
        ctx: Context,
        org_id: str,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """List customers under a reseller org.

        Paginated: returns one page (``per_page``, default 100). If a full page comes back, more may
        exist — page via ``page``/``per_page``. The total count is logged to stderr when Gandi reports it.

        Args:
            org_id: Reseller organization UUID.
            per_page: Page size.
            page: Page number.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).list_customers(org_id, per_page=per_page, page=page)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "organization"})
    async def gandi_org_get_customer(ctx: Context, org_id: str, customer_id: str) -> dict[str, Any]:
        """Retrieve a specific customer of a reseller org.

        Args:
            org_id: Reseller organization UUID.
            customer_id: Customer UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).get_customer(org_id, customer_id)
        except Exception as e:
            handle_client_error(e)


def register_organization_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write organization tools on the server."""

    @mcp.tool(
        tags={"gandi", "organization", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_org_create_customer(ctx: Context, org_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a customer under a reseller organization.

        Args:
            org_id: Reseller organization UUID.
            data: Customer payload per the Gandi organization schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create customer")
            return await get_client(ctx).create_customer(org_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "organization", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_org_update_customer(
        ctx: Context,
        org_id: str,
        customer_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a customer of a reseller organization.

        Args:
            org_id: Reseller organization UUID.
            customer_id: Customer UUID.
            data: Partial customer payload (fields to update).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update customer")
            return await get_client(ctx).update_customer(org_id, customer_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "organization", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_org_update_organization(ctx: Context, org_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an organization's profile.

        Args:
            org_id: Organization UUID.
            data: Partial organization payload (fields to update).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update organization")
            return await get_client(ctx).update_organization(org_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "organization", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_org_renew_access_token(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Renew an organization access token.

        Args:
            data: Token-renewal payload per the Gandi access-token schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "renew access token")
            return await get_client(ctx).renew_access_token(data)
        except Exception as e:
            handle_client_error(e)


def register_organization_tools(mcp: FastMCP) -> None:
    """Register every organization tool (read + write)."""
    register_organization_read_tools(mcp)
    register_organization_write_tools(mcp)
