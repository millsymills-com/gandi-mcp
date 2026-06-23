"""Mocked-integration tests for the template area tools.

Covers template list/get (GET), dispatch status (GET), create (POST), update
(PATCH), and apply (POST). Request shape, `_seg` URL-encoding, and error
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

from gandi_mcp.tools.template import register_template_read_tools, register_template_write_tools

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
    register_template_read_tools(s)
    register_template_write_tools(s)
    return s


@pytest.mark.mocked
class TestTemplateReads:
    async def test_list_templates(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"id": "t-1"}]
        route = respx_mock.get("/v5/template/templates").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_template_list_templates")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_template(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "t-1", "name": "base"}
        route = respx_mock.get("/v5/template/templates/t-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_template_get_template")
        result = await handler(ctx, template_id="t-1")

        assert route.called
        assert result == payload

    async def test_get_template_url_encodes_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/template/templates/a%2Fb").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(server, "gandi_template_get_template")
        await handler(ctx, template_id="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/template/templates/a%2Fb"

    async def test_get_dispatch(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "d-1", "state": "done"}
        route = respx_mock.get("/v5/template/dispatch/d-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_template_get_dispatch")
        result = await handler(ctx, dispatch_id="d-1")

        assert route.called
        assert result == payload

    async def test_get_template_maps_404(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.get("/v5/template/templates/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_template_get_template")
        with pytest.raises(ToolError):
            await handler(ctx, template_id="missing")


@pytest.mark.mocked
class TestCreateTemplate:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"name": "base", "payload": {}}
        payload = {"id": "t-2"}
        route = respx_mock.post("/v5/template/templates").mock(return_value=httpx.Response(201, json=payload))

        handler = await _get_handler(server, "gandi_template_create_template")
        result = await handler(ctx, data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload


@pytest.mark.mocked
class TestUpdateTemplate:
    async def test_patches_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"name": "renamed"}
        payload = {"message": "updated"}
        route = respx_mock.patch("/v5/template/templates/t-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_template_update_template")
        result = await handler(ctx, template_id="t-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == data
        assert result == payload


@pytest.mark.mocked
class TestApplyTemplate:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"domains": ["example.com"]}
        payload = {"dispatch_id": "d-9"}
        route = respx_mock.post("/v5/template/templates/t-1").mock(return_value=httpx.Response(202, json=payload))

        handler = await _get_handler(server, "gandi_template_apply_template")
        result = await handler(ctx, template_id="t-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/template/templates/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_template_apply_template")
        with pytest.raises(ToolError):
            await handler(ctx, template_id="missing", data={})
