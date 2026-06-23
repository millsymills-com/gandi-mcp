"""Mocked-integration tests for the linked-zone area tools.

Covers the read surface (domains, zones, tasks) and the write surface (zone
create/attach/update/delete, link/unlink domains). Request shape, `_seg`
URL-encoding, the 204 No Content contract, and error mapping are asserted;
gating lives in the safety-gate tests. Cassette recording is deferred to #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.linkedzone import register_linkedzone_read_tools, register_linkedzone_write_tools

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
    register_linkedzone_read_tools(s)
    register_linkedzone_write_tools(s)
    return s


@pytest.mark.mocked
class TestLinkedZoneReads:
    async def test_list_zones(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"id": "z-1"}]
        route = respx_mock.get("/v5/linkedzone/zones").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_linkedzone_list_zones")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_zone(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "z-1"}
        route = respx_mock.get("/v5/linkedzone/zones/z-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_linkedzone_get_zone")
        result = await handler(ctx, zone_id="z-1")

        assert route.called
        assert result == payload

    async def test_get_domain_url_encodes(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/linkedzone/domains/ex%2Fweird").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(server, "gandi_linkedzone_get_domain")
        await handler(ctx, domain="ex/weird")

        assert route.calls.last.request.url.raw_path == b"/v5/linkedzone/domains/ex%2Fweird"

    async def test_get_task(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "task-1", "state": "running"}
        route = respx_mock.get("/v5/linkedzone/tasks/task-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_linkedzone_get_task")
        result = await handler(ctx, task_id="task-1")

        assert route.called
        assert result == payload

    async def test_get_zone_maps_404(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.get("/v5/linkedzone/zones/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_linkedzone_get_zone")
        with pytest.raises(ToolError):
            await handler(ctx, zone_id="missing")


@pytest.mark.mocked
class TestLinkedZoneWrites:
    async def test_create_zone(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"name": "shared"}
        payload = {"id": "z-9"}
        route = respx_mock.post("/v5/linkedzone/zones").mock(return_value=httpx.Response(201, json=payload))

        handler = await _get_handler(server, "gandi_linkedzone_create_zone")
        result = await handler(ctx, data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == payload

    async def test_attach_domain(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"fqdn": "example.com"}
        route = respx_mock.post("/v5/linkedzone/zones/z-1").mock(return_value=httpx.Response(202, json={"ok": True}))

        handler = await _get_handler(server, "gandi_linkedzone_attach_domain")
        result = await handler(ctx, zone_id="z-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == {"ok": True}

    async def test_update_zone(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/linkedzone/zones/z-1").mock(return_value=httpx.Response(200, json={"ok": True}))

        handler = await _get_handler(server, "gandi_linkedzone_update_zone")
        result = await handler(ctx, zone_id="z-1", data={"name": "x"})

        assert route.calls.last.request.method == "PATCH"
        assert result == {"ok": True}

    async def test_delete_zone_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/linkedzone/zones/z-1").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_linkedzone_delete_zone")
        result = await handler(ctx, zone_id="z-1")

        assert result == {}

    async def test_link_domains(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"domains": ["a.com", "b.com"]}
        route = respx_mock.patch("/v5/linkedzone/zones/z-1/link/domains").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_linkedzone_link_domains")
        result = await handler(ctx, zone_id="z-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == data
        assert result == {"ok": True}

    async def test_unlink_domains(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"domains": ["a.com"]}
        route = respx_mock.patch("/v5/linkedzone/unlink/domains").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_linkedzone_unlink_domains")
        result = await handler(ctx, data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == data
        assert result == {"ok": True}

    async def test_create_zone_maps_400(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/linkedzone/zones").mock(return_value=httpx.Response(400, json={"cause": "bad"}))

        handler = await _get_handler(server, "gandi_linkedzone_create_zone")
        with pytest.raises(ToolError):
            await handler(ctx, data={})
