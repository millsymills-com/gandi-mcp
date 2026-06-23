"""Mocked-integration tests for the domain purchase tools (issue #158).

Covers domain restore (POST /restore) and the paid owner-contact change
(PUT /contacts/owner). Request shape, `_seg` URL-encoding, and error mapping
are asserted; gating lives in the safety-gate tests. Cassette recording is the
human follow-up (purchase endpoints — do not auto-record).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.domain import register_domain_purchase_tools

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
    register_domain_purchase_tools(s)
    return s


@pytest.mark.mocked
class TestRestoreDomain:
    async def test_posts_duration_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "restored"}
        route = respx_mock.post("/v5/domain/domains/example.com/restore").mock(
            return_value=httpx.Response(202, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_restore")
        result = await handler(ctx, fqdn="example.com", duration=2, currency="USD")

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"duration": 2, "currency": "USD"}
        assert result == payload

    async def test_omits_currency_when_unset(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/domain/domains/example.com/restore").mock(
            return_value=httpx.Response(202, json={})
        )

        handler = await _get_handler(server, "gandi_domain_restore")
        await handler(ctx, fqdn="example.com")

        assert json.loads(route.calls.last.request.content) == {"duration": 1}

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/domain/domains/ex%2Fweird/restore").mock(return_value=httpx.Response(202, json={}))

        handler = await _get_handler(server, "gandi_domain_restore")
        await handler(ctx, fqdn="ex/weird")

        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/restore"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/domain/domains/missing.com/restore").mock(
            return_value=httpx.Response(404, json={"cause": "not in redemption"})
        )

        handler = await _get_handler(server, "gandi_domain_restore")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")


@pytest.mark.mocked
class TestUpdateOwnerContact:
    async def test_puts_owner_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        owner = {"given": "Ada", "family": "Lovelace", "email": "ada@example.com"}
        payload = {"message": "owner change initiated"}
        route = respx_mock.put("/v5/domain/domains/example.com/contacts/owner").mock(
            return_value=httpx.Response(202, json=payload)
        )

        handler = await _get_handler(server, "gandi_domain_update_owner_contact")
        result = await handler(ctx, fqdn="example.com", owner=owner)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"owner": owner}
        assert result == payload

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.put("/v5/domain/domains/ex%2Fweird/contacts/owner").mock(
            return_value=httpx.Response(202, json={})
        )

        handler = await _get_handler(server, "gandi_domain_update_owner_contact")
        await handler(ctx, fqdn="ex/weird", owner={})

        assert route.calls.last.request.url.raw_path == b"/v5/domain/domains/ex%2Fweird/contacts/owner"

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/domain/domains/example.com/contacts/owner").mock(
            return_value=httpx.Response(400, json={"cause": "invalid contact"})
        )

        handler = await _get_handler(server, "gandi_domain_update_owner_contact")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", owner={})
