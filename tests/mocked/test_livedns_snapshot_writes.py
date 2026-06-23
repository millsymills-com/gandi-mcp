"""Mocked-integration tests for the LiveDNS zone-snapshot write tools.

Covers create (POST), rename (PATCH), and delete (DELETE) of zone snapshots.
Request shape (method, URL, body), `_seg` URL-encoding, the 204 No Content
contract, and error mapping are asserted; gating lives in the safety-gate tests.
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
class TestCreateSnapshot:
    async def test_posts_name_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "snap-1", "name": "before-migration"}
        route = respx_mock.post("/v5/livedns/domains/example.com/snapshots").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_create_snapshot")
        result = await handler(ctx, fqdn="example.com", name="before-migration")

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"name": "before-migration"}
        assert result == payload

    async def test_omits_name_when_not_given(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/livedns/domains/example.com/snapshots").mock(
            return_value=httpx.Response(201, json={"id": "snap-2"})
        )

        handler = await _get_handler(server, "gandi_livedns_create_snapshot")
        await handler(ctx, fqdn="example.com")

        assert route.called
        assert json.loads(route.calls.last.request.content) == {}

    async def test_url_encodes_fqdn(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/livedns/domains/ex%2Fweird/snapshots").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_create_snapshot")
        await handler(ctx, fqdn="ex/weird")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/ex%2Fweird/snapshots"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/livedns/domains/missing.com/snapshots").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_livedns_create_snapshot")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com")


@pytest.mark.mocked
class TestUpdateSnapshot:
    async def test_patches_name_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "snap-1", "name": "renamed"}
        route = respx_mock.patch("/v5/livedns/domains/example.com/snapshots/snap-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_update_snapshot")
        result = await handler(ctx, fqdn="example.com", snapshot_id="snap-1", name="renamed")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"name": "renamed"}
        assert result == payload

    async def test_url_encodes_snapshot_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/livedns/domains/example.com/snapshots/a%2Fb").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_update_snapshot")
        await handler(ctx, fqdn="example.com", snapshot_id="a/b", name="x")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/snapshots/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/livedns/domains/example.com/snapshots/missing").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_update_snapshot")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", snapshot_id="missing", name="x")


@pytest.mark.mocked
class TestDeleteSnapshot:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/livedns/domains/example.com/snapshots/snap-1").mock(
            return_value=httpx.Response(200, json={"message": "Deleted"})
        )

        handler = await _get_handler(server, "gandi_livedns_delete_snapshot")
        result = await handler(ctx, fqdn="example.com", snapshot_id="snap-1")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "Deleted"}

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        """Gandi commonly returns 204 No Content on snapshot delete — maps to ``{}``."""
        respx_mock.delete("/v5/livedns/domains/example.com/snapshots/snap-1").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_livedns_delete_snapshot")
        result = await handler(ctx, fqdn="example.com", snapshot_id="snap-1")

        assert result == {}

    async def test_url_encodes_snapshot_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/livedns/domains/example.com/snapshots/a%2Fb").mock(
            return_value=httpx.Response(204)
        )

        handler = await _get_handler(server, "gandi_livedns_delete_snapshot")
        await handler(ctx, fqdn="example.com", snapshot_id="a/b")

        assert route.called
        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/snapshots/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/livedns/domains/example.com/snapshots/missing").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_delete_snapshot")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", snapshot_id="missing")
