"""Mocked-integration tests for LiveDNS DNSSEC-restore and TSIG-create writes.

Covers DNSSEC key restore (PATCH) and AXFR TSIG key creation (POST). Request
shape, `_seg` URL-encoding, and error mapping are asserted; gating lives in
the safety-gate tests. Cassette recording is deferred to issue #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.livedns import register_livedns_write_tools

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
    register_livedns_write_tools(s)
    return s


@pytest.mark.mocked
class TestRestoreDNSSECKey:
    async def test_patches_deleted_false_and_returns_payload(
        self, ctx: AsyncMock, respx_mock: Any, server: FastMCP
    ) -> None:
        payload = {"id": "key-1", "deleted": False}
        route = respx_mock.patch("/v5/livedns/domains/example.com/keys/key-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_restore_dnssec_key")
        result = await handler(ctx, fqdn="example.com", key_id="key-1")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"deleted": False}
        assert result == payload

    async def test_url_encodes_key_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/livedns/domains/example.com/keys/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_restore_dnssec_key")
        await handler(ctx, fqdn="example.com", key_id="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/keys/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/livedns/domains/example.com/keys/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_livedns_restore_dnssec_key")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", key_id="missing")


@pytest.mark.mocked
class TestCreateTSIGKey:
    async def test_posts_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "tsig-1", "name": "key.", "secret": "abc=="}
        route = respx_mock.post("/v5/livedns/axfr/tsig").mock(return_value=httpx.Response(201, json=payload))

        handler = await _get_handler(server, "gandi_livedns_create_tsig_key")
        result = await handler(ctx)

        assert route.called
        assert route.calls.last.request.method == "POST"
        assert result == payload

    async def test_maps_403_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/livedns/axfr/tsig").mock(return_value=httpx.Response(403, json={"cause": "Forbidden"}))

        handler = await _get_handler(server, "gandi_livedns_create_tsig_key")
        with pytest.raises(ToolError):
            await handler(ctx)
