"""Template tools (/v5/template) — domain-configuration templates + dispatch."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_readwrite, get_client


def register_template_read_tools(mcp: FastMCP) -> None:
    """Register read-only template tools on the server."""

    @mcp.tool(tags={"gandi", "template"})
    async def gandi_template_list_templates(ctx: Context) -> list[dict[str, Any]]:
        """List domain-configuration templates.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).template_list_templates()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "template"})
    async def gandi_template_get_template(ctx: Context, template_id: str) -> dict[str, Any]:
        """Get a single domain-configuration template by id.

        Args:
            template_id: Template UUID.


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).template_get_template(template_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "template"})
    async def gandi_template_get_dispatch(ctx: Context, dispatch_id: str) -> dict[str, Any]:
        """Get the status of a template dispatch (application) operation.

        Args:
            dispatch_id: Dispatch UUID returned when a template is applied.


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).template_get_dispatch(dispatch_id)
        except Exception as e:
            handle_client_error(e)


def register_template_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write template tools on the server."""

    @mcp.tool(
        tags={"gandi", "template", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_template_create_template(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Create a domain-configuration template.

        Args:
            data: Template payload per the Gandi template schema.


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "create template")
            return await get_client(ctx).template_create_template(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "template", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_template_update_template(ctx: Context, template_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a domain-configuration template.

        Args:
            template_id: Template UUID.
            data: Partial template payload (fields to update).


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update template")
            return await get_client(ctx).template_update_template(template_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "template", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_template_apply_template(ctx: Context, template_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Apply a template to one or more domains.

        Args:
            template_id: Template UUID to apply.
            data: Dispatch payload (target domains and options) per the Gandi
                template schema.


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "apply template")
            return await get_client(ctx).template_apply_template(template_id, data)
        except Exception as e:
            handle_client_error(e)


def register_template_tools(mcp: FastMCP) -> None:
    """Register every template tool (read + write)."""
    register_template_read_tools(mcp)
    register_template_write_tools(mcp)
