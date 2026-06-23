"""Mocked-integration tests for the LiveDNS read-backfill tools.

Reads only (GET, no request body) — paths confirmed against the live Gandi
RAML in docs/superpowers/plans/2026-06-23-tool-coverage-90pct.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.livedns import register_livedns_read_tools

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
    register_livedns_read_tools(s)
    return s


@pytest.mark.mocked
class TestLiveDNSGetDNSSECKey:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "key-1", "flags": 257}
        route = respx_mock.get("/v5/livedns/domains/example.com/keys/key-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_get_dnssec_key")
        result = await handler(ctx, fqdn="example.com", key_id="key-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_url_encodes_key_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/livedns/domains/example.com/keys/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_get_dnssec_key")
        await handler(ctx, fqdn="example.com", key_id="a/b")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/keys/a%2Fb"


@pytest.mark.mocked
class TestLiveDNSSnapshots:
    async def test_list_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"id": "snap-1", "name": "before-migration"}]
        route = respx_mock.get("/v5/livedns/domains/example.com/snapshots").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_list_snapshots")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload

    async def test_get_calls_id_scoped_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "snap-1", "zone_data": []}
        route = respx_mock.get("/v5/livedns/domains/example.com/snapshots/snap-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_get_snapshot")
        result = await handler(ctx, fqdn="example.com", snapshot_id="snap-1")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestLiveDNSGenericNameservers:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"nameservers": ["ns-1.gandi.net", "ns-2.gandi.net"]}
        route = respx_mock.get("/v5/livedns/nameservers/example.com").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_get_generic_nameservers")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestLiveDNSTSIGKeys:
    async def test_list_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"id": "tsig-1", "name": "key1"}]
        route = respx_mock.get("/v5/livedns/axfr/tsig").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_livedns_list_tsig_keys")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_calls_id_scoped_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "tsig-1", "secret": "redacted"}
        route = respx_mock.get("/v5/livedns/axfr/tsig/tsig-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_livedns_get_tsig_key")
        result = await handler(ctx, tsig_id="tsig-1")

        assert route.called
        assert result == payload
