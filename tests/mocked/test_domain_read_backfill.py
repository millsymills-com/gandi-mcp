"""Mocked-integration tests for the domain read-backfill tools.

Reads only (GET, no request body) — paths confirmed against the live Gandi
RAML in docs/superpowers/plans/2026-06-23-tool-coverage-90pct.md. Write/purchase
tools in the same areas land separately once request shapes are confirmed at
cassette-recording time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.domain import register_domain_read_tools

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
    register_domain_read_tools(s)
    return s


@pytest.mark.mocked
class TestDomainListTags:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = ["prod", "billing"]
        route = respx_mock.get("/v5/domain/domains/example.com/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_list_tags")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/domain/domains/ex%2Fweird/tags").mock(return_value=httpx.Response(200, json=[]))

        handler = await _get_handler(server, "gandi_domain_list_tags")
        await handler(ctx, fqdn="ex/weird")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/tags"


@pytest.mark.mocked
class TestDomainGetRestoreInfo:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"restorable": True, "price": {"amount": 80.0, "currency": "USD"}}
        route = respx_mock.get("/v5/domain/domains/example.com/restore").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_get_restore_info")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestDomainWebRedirections:
    async def test_list_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"host": "www", "type": "http301", "url": "https://example.com"}]
        route = respx_mock.get("/v5/domain/domains/example.com/webredirs").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_list_web_redirections")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload

    async def test_get_calls_host_scoped_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"host": "www", "type": "http301", "url": "https://example.com"}
        route = respx_mock.get("/v5/domain/domains/example.com/webredirs/www").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_get_web_redirection")
        result = await handler(ctx, fqdn="example.com", host="www")

        assert route.called
        assert result == payload

    async def test_get_url_encodes_host(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/domain/domains/example.com/webredirs/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_domain_get_web_redirection")
        await handler(ctx, fqdn="example.com", host="a/b")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/example.com/webredirs/a%2Fb"


@pytest.mark.mocked
class TestDomainCheckTransferinAvailable:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"available": True}
        route = respx_mock.get("/v5/domain/transferin/example.com/available").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_check_transferin_available")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestDomainGetCreateStatus:
    async def test_calls_endpoint_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"step": "done"}
        route = respx_mock.get("/v5/domain/domains/example.com/createstatus").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_get_create_status")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestDomainLiveDNS:
    async def test_get_livedns_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"current": "livedns"}
        route = respx_mock.get("/v5/domain/domains/example.com/livedns").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_get_livedns")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload

    async def test_get_livedns_dnssec_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"status": "enabled"}
        route = respx_mock.get("/v5/domain/domains/example.com/livedns/dnssec").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_get_livedns_dnssec")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestDomainTLDs:
    async def test_list_tlds_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"name": "com"}, {"name": "net"}]
        route = respx_mock.get("/v5/domain/tlds").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_domain_list_tlds")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_tld_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"name": "com", "category": "gTLD"}
        route = respx_mock.get("/v5/domain/tlds/com").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_domain_get_tld")
        result = await handler(ctx, name="com")

        assert route.called
        assert result == payload
