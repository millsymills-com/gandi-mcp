"""Comment tools (/v5/comment) — generic per-object comments."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import assert_readwrite, get_client


def register_comment_read_tools(mcp: FastMCP) -> None:
    """Register read-only comment tools on the server."""

    @mcp.tool(tags={"gandi", "comment"})
    async def gandi_comment_get(ctx: Context, comment_id: str) -> dict[str, Any]:
        """Get the comment attached to a Gandi object.

        Args:
            comment_id: ID of the comment (object-scoped).


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).get_comment(comment_id)
        except Exception as e:
            handle_client_error(e)


def register_comment_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write comment tools on the server."""

    @mcp.tool(
        tags={"gandi", "comment", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_comment_set(ctx: Context, comment_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Set (create or overwrite) the comment on a Gandi object.

        Args:
            comment_id: ID of the comment (object-scoped).
            data: Comment payload per the Gandi comment schema.


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "set comment")
            return await get_client(ctx).set_comment(comment_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "comment", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_comment_delete(ctx: Context, comment_id: str) -> dict[str, Any]:
        """Delete the comment on a Gandi object.

        Args:
            comment_id: ID of the comment (object-scoped).


        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete comment")
            return await get_client(ctx).delete_comment(comment_id)
        except Exception as e:
            handle_client_error(e)


def register_comment_tools(mcp: FastMCP) -> None:
    """Register every comment tool (read + write)."""
    register_comment_read_tools(mcp)
    register_comment_write_tools(mcp)
