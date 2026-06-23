"""Mocked-integration tests for the comment area tools.

Covers get (GET), set (POST), and delete (DELETE) of a per-object comment.
Request shape, `_seg` URL-encoding, the 204 No Content contract, and error
mapping are asserted; gating lives in the safety-gate tests. Cassette
recording is deferred to issue #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.comment import register_comment_read_tools, register_comment_write_tools

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


async def _get_handler(server: FastMCP, name: str) -> Any:
    tool = await server.get_tool(name)
    assert tool is not None, f"tool {name!r} not registered"
    assert isinstance(tool, FunctionTool), f"tool {name!r} is not a FunctionTool"
    return tool.fn


@pytest.fixture
def server() -> FastMCP:
    s = FastMCP(name="t")
    register_comment_read_tools(s)
    register_comment_write_tools(s)
    return s


@pytest.mark.mocked
class TestGetComment:
    async def test_gets_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "c-1", "body": "hello"}
        route = respx_mock.get("/v5/comment/comments/c-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_comment_get")
        result = await handler(ctx, comment_id="c-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_url_encodes_comment_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/comment/comments/a%2Fb").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(server, "gandi_comment_get")
        await handler(ctx, comment_id="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/comment/comments/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.get("/v5/comment/comments/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_comment_get")
        with pytest.raises(ToolError):
            await handler(ctx, comment_id="missing")


@pytest.mark.mocked
class TestSetComment:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"body": "a note"}
        payload = {"message": "set"}
        route = respx_mock.post("/v5/comment/comments/c-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_comment_set")
        result = await handler(ctx, comment_id="c-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/comment/comments/c-1").mock(return_value=httpx.Response(400, json={"cause": "bad"}))

        handler = await _get_handler(server, "gandi_comment_set")
        with pytest.raises(ToolError):
            await handler(ctx, comment_id="c-1", data={})


@pytest.mark.mocked
class TestDeleteComment:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/comment/comments/c-1").mock(
            return_value=httpx.Response(200, json={"message": "deleted"})
        )

        handler = await _get_handler(server, "gandi_comment_delete")
        result = await handler(ctx, comment_id="c-1")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "deleted"}

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/comment/comments/c-1").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_comment_delete")
        result = await handler(ctx, comment_id="c-1")

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/comment/comments/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_comment_delete")
        with pytest.raises(ToolError):
            await handler(ctx, comment_id="missing")
