"""Mocked-integration tests for the organization write tools.

Covers customer create (POST), customer update (PATCH), organization update
(PATCH), and access-token renewal (POST). Request shape, `_seg` URL-encoding,
and error mapping are asserted; gating lives in the safety-gate tests.
Cassette recording is deferred to issue #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.organization import register_organization_write_tools

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
    register_organization_write_tools(s)
    return s


@pytest.mark.mocked
class TestCreateCustomer:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"name": "Acme", "email": "acme@example.com", "type": "company"}
        payload = {"id": "cust-1"}
        route = respx_mock.post("/v5/organization/organizations/org-1/customers").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_org_create_customer")
        result = await handler(ctx, org_id="org-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_url_encodes_org_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/organization/organizations/a%2Fb/customers").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_org_create_customer")
        await handler(ctx, org_id="a/b", data={})

        assert route.calls.last.request.url.raw_path == b"/v5/organization/organizations/a%2Fb/customers"

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/organization/organizations/org-1/customers").mock(
            return_value=httpx.Response(400, json={"cause": "bad"})
        )

        handler = await _get_handler(server, "gandi_org_create_customer")
        with pytest.raises(ToolError):
            await handler(ctx, org_id="org-1", data={})


@pytest.mark.mocked
class TestUpdateCustomer:
    async def test_patches_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"email": "new@example.com"}
        payload = {"message": "updated"}
        route = respx_mock.patch("/v5/organization/organizations/org-1/customers/cust-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_org_update_customer")
        result = await handler(ctx, org_id="org-1", customer_id="cust-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/organization/organizations/org-1/customers/missing").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_org_update_customer")
        with pytest.raises(ToolError):
            await handler(ctx, org_id="org-1", customer_id="missing", data={})


@pytest.mark.mocked
class TestUpdateOrganization:
    async def test_patches_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"email": "org@example.com"}
        payload = {"message": "updated"}
        route = respx_mock.patch("/v5/organization/organizations/org-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_org_update_organization")
        result = await handler(ctx, org_id="org-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == data
        assert result == payload


@pytest.mark.mocked
class TestRenewAccessToken:
    async def test_posts_data_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"refresh_token": "rt-1"}
        payload = {"access_token": "at-2"}
        route = respx_mock.post("/v5/organization/access-tokens").mock(return_value=httpx.Response(201, json=payload))

        handler = await _get_handler(server, "gandi_org_renew_access_token")
        result = await handler(ctx, data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_maps_403_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/organization/access-tokens").mock(
            return_value=httpx.Response(403, json={"cause": "forbidden"})
        )

        handler = await _get_handler(server, "gandi_org_renew_access_token")
        with pytest.raises(ToolError):
            await handler(ctx, data={})
