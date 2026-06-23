"""Mocked-integration tests for the domain LiveDNS enablement write tools.

Covers registry-side LiveDNS enablement (POST) and LiveDNS-managed DNSSEC
activate (POST) / disable (DELETE). Request shape, `_seg` URL-encoding, the
204 No Content contract, and error mapping are asserted; gating lives in the
safety-gate tests. Cassette recording is deferred to issue #102.
"""

from __future__ import annotations

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
class TestEnableLiveDNS:
    async def test_posts_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "LiveDNS enabled"}
        route = respx_mock.post("/v5/domain/domains/example.com/livedns").mock(
            return_value=httpx.Response(202, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_enable_livedns")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert route.calls.last.request.method == "POST"
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/domain/domains/ex%2Fweird/livedns").mock(return_value=httpx.Response(202, json={}))

        handler = await _get_handler(server, "gandi_domain_enable_livedns")
        await handler(ctx, fqdn="ex/weird")

        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/livedns"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/domain/domains/missing.com/livedns").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_domain_enable_livedns")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")


@pytest.mark.mocked
class TestActivateLiveDNSDNSSEC:
    async def test_posts_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "DNSSEC activated"}
        route = respx_mock.post("/v5/domain/domains/example.com/livedns/dnssec").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_activate_livedns_dnssec")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert route.calls.last.request.method == "POST"
        assert result == payload

    async def test_maps_409_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/domain/domains/example.com/livedns/dnssec").mock(
            return_value=httpx.Response(409, json={"cause": "already active"})
        )

        handler = await _get_handler(server, "gandi_domain_activate_livedns_dnssec")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com")


@pytest.mark.mocked
class TestDisableLiveDNSDNSSEC:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/domain/domains/example.com/livedns/dnssec").mock(
            return_value=httpx.Response(200, json={"message": "DNSSEC disabled"})
        )

        handler = await _get_handler(server, "gandi_domain_disable_livedns_dnssec")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "DNSSEC disabled"}

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/domain/domains/example.com/livedns/dnssec").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_domain_disable_livedns_dnssec")
        result = await handler(ctx, fqdn="example.com")

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/domain/domains/example.com/livedns/dnssec").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_domain_disable_livedns_dnssec")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com")
