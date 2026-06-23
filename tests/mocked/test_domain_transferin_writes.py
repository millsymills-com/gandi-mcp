"""Mocked-integration tests for the domain transfer-in and remaining writes.

Covers transfer-in relaunch (PUT), authinfo update (PUT), FOA resend (POST),
registry DS-record replace (PUT), trademark-claim accept (POST), and
reachability relaunch (PATCH). Request shape, `_seg` URL-encoding, and error
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
class TestRelaunchTransferIn:
    async def test_puts_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "relaunched"}
        route = respx_mock.put("/v5/domain/transferin/example.com").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_domain_relaunch_transferin")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {}
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.put("/v5/domain/transferin/ex%2Fweird").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(server, "gandi_domain_relaunch_transferin")
        await handler(ctx, fqdn="ex/weird")

        request = route.calls.last.request
        assert request.url.raw_path == b"/v5/domain/transferin/ex%2Fweird"
        assert json.loads(request.content) == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/domain/transferin/missing.com").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_domain_relaunch_transferin")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")


@pytest.mark.mocked
class TestUpdateTransferInAuthinfo:
    async def test_puts_authinfo_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "updated"}
        route = respx_mock.put("/v5/domain/transferin/example.com/authinfo").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_update_transferin_authinfo")
        result = await handler(ctx, fqdn="example.com", authinfo="abc123")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"authinfo": "abc123"}
        assert result == payload


@pytest.mark.mocked
class TestResendTransferInFOA:
    async def test_posts_email_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "sent"}
        route = respx_mock.post("/v5/domain/transferin/example.com/foa").mock(
            return_value=httpx.Response(202, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_resend_transferin_foa")
        result = await handler(ctx, fqdn="example.com", email="owner@example.com")

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"email": "owner@example.com"}
        assert result == payload


@pytest.mark.mocked
class TestReplaceDNSSECKeys:
    async def test_puts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"keys": [{"flags": 257, "algorithm": 13, "public_key": "AAAA"}]}
        payload = {"message": "replaced"}
        route = respx_mock.put("/v5/domain/domains/example.com/dnskeys").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_replace_dnssec_keys")
        result = await handler(ctx, fqdn="example.com", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/domain/domains/example.com/dnskeys").mock(
            return_value=httpx.Response(400, json={"cause": "bad key"})
        )

        handler = await _get_handler(server, "gandi_domain_replace_dnssec_keys")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", data={})


@pytest.mark.mocked
class TestAcceptClaim:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"accept": True}
        payload = {"message": "accepted"}
        route = respx_mock.post("/v5/domain/domains/example.com/claims").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_accept_claim")
        result = await handler(ctx, fqdn="example.com", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload


@pytest.mark.mocked
class TestRelaunchReachability:
    async def test_patches_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "relaunched"}
        route = respx_mock.patch("/v5/domain/domains/example.com/reachability").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_relaunch_reachability")
        result = await handler(ctx, fqdn="example.com")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {}
        assert result == payload

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/domain/domains/missing.com/reachability").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_domain_relaunch_reachability")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")
