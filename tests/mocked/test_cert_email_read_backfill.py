"""Mocked-integration tests for certificate + email read-backfill tools.

Reads only (GET, no request body) — paths confirmed against the live Gandi
RAML in docs/superpowers/plans/2026-06-23-tool-coverage-90pct.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.certificate import register_certificate_read_tools
from gandi_mcp.tools.email import register_email_read_tools

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


async def _get_handler(server: FastMCP, name: str) -> Any:
    tool = await server.get_tool(name)
    assert tool is not None, f"tool {name!r} not registered"
    assert isinstance(tool, FunctionTool), f"tool {name!r} is not a FunctionTool"
    return tool.fn


@pytest.fixture
def cert_server() -> FastMCP:
    s = FastMCP(name="t")
    register_certificate_read_tools(s)
    return s


@pytest.fixture
def email_server() -> FastMCP:
    s = FastMCP(name="t")
    register_email_read_tools(s)
    return s


@pytest.mark.mocked
class TestCertListTags:
    async def test_calls_endpoint_and_returns_payload(
        self, ctx: AsyncMock, respx_mock: Any, cert_server: FastMCP
    ) -> None:
        payload = ["prod", "renewal"]
        route = respx_mock.get("/v5/certificate/issued-certs/cert-1/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(cert_server, "gandi_cert_list_tags")
        result = await handler(ctx, cert_id="cert-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, cert_server: FastMCP) -> None:
        route = respx_mock.get("/v5/certificate/issued-certs/a%2Fb/tags").mock(
            return_value=httpx.Response(200, json=[])
        )

        handler = await _get_handler(cert_server, "gandi_cert_list_tags")
        await handler(ctx, cert_id="a/b")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb/tags"


@pytest.mark.mocked
class TestCertPackages:
    async def test_list_calls_endpoint(self, ctx: AsyncMock, respx_mock: Any, cert_server: FastMCP) -> None:
        payload = [{"name": "cert_std_1_0_0"}]
        route = respx_mock.get("/v5/certificate/packages").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(cert_server, "gandi_cert_list_packages")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_calls_name_scoped_endpoint(self, ctx: AsyncMock, respx_mock: Any, cert_server: FastMCP) -> None:
        payload = {"name": "cert_std_1_0_0", "max_year": 1}
        route = respx_mock.get("/v5/certificate/packages/cert_std_1_0_0").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(cert_server, "gandi_cert_get_package")
        result = await handler(ctx, name="cert_std_1_0_0")

        assert route.called
        assert result == payload


@pytest.mark.mocked
class TestEmailGetOffer:
    async def test_calls_endpoint_and_returns_payload(
        self, ctx: AsyncMock, respx_mock: Any, email_server: FastMCP
    ) -> None:
        payload = {"version": 2, "quota": 50}
        route = respx_mock.get("/v5/email/offers/example.com").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(email_server, "gandi_email_get_offer")
        result = await handler(ctx, domain="example.com")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_url_encodes_domain(self, ctx: AsyncMock, respx_mock: Any, email_server: FastMCP) -> None:
        route = respx_mock.get("/v5/email/offers/ex%2Fweird").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(email_server, "gandi_email_get_offer")
        await handler(ctx, domain="ex/weird")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/email/offers/ex%2Fweird"
