"""Mocked-integration tests for the domain web-redirection write tools.

Covers create (POST), update (PATCH), and delete (DELETE) of web redirections.
Each test asserts request method, URL, and body pass-through, plus `_seg`
URL-encoding and error mapping. Cassette recording is deferred to issue #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.domain import register_domain_write_tools

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
    register_domain_write_tools(s)
    return s


@pytest.mark.mocked
class TestCreateWebRedirection:
    async def test_posts_body_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"host": "www", "type": "http301", "target": "https://example.com"}
        payload = {"message": "Created"}
        route = respx_mock.post("/v5/domain/domains/example.com/webredirs").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_create_web_redirection")
        result = await handler(ctx, fqdn="example.com", data=data)

        assert route.called
        assert route.calls.last.request.method == "POST"
        assert json.loads(route.calls.last.request.content) == data
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/domain/domains/ex%2Fweird/webredirs").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_domain_create_web_redirection")
        await handler(ctx, fqdn="ex/weird", data={"host": "www"})

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/webredirs"

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/domain/domains/example.com/webredirs").mock(
            return_value=httpx.Response(400, json={"cause": "Bad Request"})
        )

        handler = await _get_handler(server, "gandi_domain_create_web_redirection")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", data={"host": "www"})


@pytest.mark.mocked
class TestUpdateWebRedirection:
    async def test_patches_body_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"target": "https://new.example.com"}
        payload = {"message": "Updated"}
        route = respx_mock.patch("/v5/domain/domains/example.com/webredirs/www").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_update_web_redirection")
        result = await handler(ctx, fqdn="example.com", host="www", data=data)

        assert route.called
        assert route.calls.last.request.method == "PATCH"
        assert json.loads(route.calls.last.request.content) == data
        assert result == payload

    async def test_url_encodes_host(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/domain/domains/example.com/webredirs/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_domain_update_web_redirection")
        await handler(ctx, fqdn="example.com", host="a/b", data={})

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/example.com/webredirs/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/domain/domains/example.com/webredirs/www").mock(
            return_value=httpx.Response(404, json={"cause": "not found"})
        )

        handler = await _get_handler(server, "gandi_domain_update_web_redirection")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", host="www", data={})


@pytest.mark.mocked
class TestDeleteWebRedirection:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/domain/domains/example.com/webredirs/www").mock(
            return_value=httpx.Response(202, json={"message": "Deleted"})
        )

        handler = await _get_handler(server, "gandi_domain_delete_web_redirection")
        result = await handler(ctx, fqdn="example.com", host="www")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "Deleted"}

    async def test_url_encodes_host(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/domain/domains/example.com/webredirs/a%2Fb").mock(
            return_value=httpx.Response(204)
        )

        handler = await _get_handler(server, "gandi_domain_delete_web_redirection")
        await handler(ctx, fqdn="example.com", host="a/b")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/example.com/webredirs/a%2Fb"

    async def test_deletes_204_returns_empty_dict(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        """Gandi returns 204 No Content on webredir delete — client maps it to ``{}``."""
        respx_mock.delete("/v5/domain/domains/example.com/webredirs/www").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_domain_delete_web_redirection")
        result = await handler(ctx, fqdn="example.com", host="www")

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/domain/domains/example.com/webredirs/www").mock(
            return_value=httpx.Response(404, json={"cause": "not found"})
        )

        handler = await _get_handler(server, "gandi_domain_delete_web_redirection")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", host="www")
