"""Mocked-integration tests for the domain tag write tools.

Covers create (POST), replace (PUT), update (PATCH), and delete (DELETE) of the
operator-defined tags on a domain. Request shape (method, URL, body) and the
pass-through response are asserted; gating lives in the safety-gate tests.
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
class TestDomainCreateTag:
    async def test_posts_name_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tag created"}
        route = respx_mock.post("/v5/domain/domains/example.com/tags").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_create_tag")
        result = await handler(ctx, fqdn="example.com", name="prod")

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"name": "prod"}
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/domain/domains/ex%2Fweird/tags").mock(return_value=httpx.Response(201, json={}))

        handler = await _get_handler(server, "gandi_domain_create_tag")
        await handler(ctx, fqdn="ex/weird", name="prod")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/tags"


@pytest.mark.mocked
class TestDomainReplaceTags:
    async def test_puts_tags_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tags replaced"}
        route = respx_mock.put("/v5/domain/domains/example.com/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_replace_tags")
        result = await handler(ctx, fqdn="example.com", tags=["prod", "billing"])

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"tags": ["prod", "billing"]}
        assert result == payload


@pytest.mark.mocked
class TestDomainUpdateTags:
    async def test_patches_tags_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tags added"}
        route = respx_mock.patch("/v5/domain/domains/example.com/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_update_tags")
        result = await handler(ctx, fqdn="example.com", tags=["staging"])

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"tags": ["staging"]}
        assert result == payload


@pytest.mark.mocked
class TestDomainDeleteTags:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/domain/domains/example.com/tags").mock(
            return_value=httpx.Response(200, json={"message": "Tags removed"})
        )

        handler = await _get_handler(server, "gandi_domain_delete_tags")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "Tags removed"}


@pytest.mark.mocked
class TestDomainTagWriteErrorPaths:
    async def test_create_tag_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/domain/domains/missing.com/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_domain_create_tag")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com", name="prod")

    async def test_delete_tags_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/domain/domains/missing.com/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_domain_delete_tags")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")
