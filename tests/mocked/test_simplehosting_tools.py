"""Mocked-integration tests for the Simple Hosting area tools.

Covers the read surface (instances, vhosts, usage), the free-write surface
(instance delete/action, vhost create/delete/update/purge), and the gated
purchase surface (instance create/update). Request shape, `_seg` URL-encoding,
the 204 No Content contract, and error mapping are asserted; gating itself
lives in the safety-gate tests. Cassette recording is deferred to #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.simplehosting import register_simplehosting_tools

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
    register_simplehosting_tools(s)
    return s


@pytest.mark.mocked
class TestSimpleHostingReads:
    async def test_list_instances(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"id": "i-1"}]
        route = respx_mock.get("/v5/simplehosting/instances").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_simplehosting_list_instances")
        result = await handler(ctx)

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_get_instance(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "i-1"}
        route = respx_mock.get("/v5/simplehosting/instances/i-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_simplehosting_get_instance")
        result = await handler(ctx, instance_id="i-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_list_vhosts(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"fqdn": "site.example.com"}]
        route = respx_mock.get("/v5/simplehosting/instances/i-1/vhosts").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_simplehosting_list_vhosts")
        result = await handler(ctx, instance_id="i-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == payload

    async def test_list_vhosts_url_encodes(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/simplehosting/instances/i%2F1/vhosts").mock(
            return_value=httpx.Response(200, json=[])
        )

        handler = await _get_handler(server, "gandi_simplehosting_list_vhosts")
        await handler(ctx, instance_id="i/1")

        assert route.calls.last.request.url.raw_path == b"/v5/simplehosting/instances/i%2F1/vhosts"

    async def test_get_vhost_url_encodes(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/simplehosting/instances/i-1/vhosts/ex%2Fweird").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(server, "gandi_simplehosting_get_vhost")
        await handler(ctx, instance_id="i-1", fqdn="ex/weird")

        assert route.calls.last.request.url.raw_path == b"/v5/simplehosting/instances/i-1/vhosts/ex%2Fweird"

    async def test_get_instance_usage(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"cpu": 0.1}
        route = respx_mock.get("/v5/simplehosting/instances/i-1/usage").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_simplehosting_get_instance_usage")
        result = await handler(ctx, instance_id="i-1")

        assert route.called
        assert result == payload

    async def test_get_instance_maps_404(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.get("/v5/simplehosting/instances/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_simplehosting_get_instance")
        with pytest.raises(ToolError):
            await handler(ctx, instance_id="missing")

    @pytest.mark.parametrize(
        ("tool_name", "path", "kwargs"),
        [
            ("gandi_simplehosting_list_instances", "/v5/simplehosting/instances", {}),
            ("gandi_simplehosting_list_vhosts", "/v5/simplehosting/instances/i-1/vhosts", {"instance_id": "i-1"}),
            (
                "gandi_simplehosting_get_vhost",
                "/v5/simplehosting/instances/i-1/vhosts/site.example.com",
                {"instance_id": "i-1", "fqdn": "site.example.com"},
            ),
            ("gandi_simplehosting_get_instance_usage", "/v5/simplehosting/instances/i-1/usage", {"instance_id": "i-1"}),
        ],
    )
    async def test_read_handler_maps_error(
        self,
        ctx: AsyncMock,
        respx_mock: Any,
        server: FastMCP,
        tool_name: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        respx_mock.get(path).mock(return_value=httpx.Response(500, json={}))

        handler = await _get_handler(server, tool_name)
        with pytest.raises(ToolError):
            await handler(ctx, **kwargs)


@pytest.mark.mocked
class TestSimpleHostingWrites:
    async def test_delete_instance_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/simplehosting/instances/i-1").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_simplehosting_delete_instance")
        result = await handler(ctx, instance_id="i-1")

        assert result == {}

    async def test_perform_instance_action(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"action": "restart"}
        route = respx_mock.post("/v5/simplehosting/instances/i-1/action").mock(
            return_value=httpx.Response(202, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_simplehosting_perform_instance_action")
        result = await handler(ctx, instance_id="i-1", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == {"ok": True}

    async def test_create_vhost(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"fqdn": "site.example.com"}
        route = respx_mock.post("/v5/simplehosting/instances/i-1/vhosts").mock(
            return_value=httpx.Response(201, json={"id": "v-1"})
        )

        handler = await _get_handler(server, "gandi_simplehosting_create_vhost")
        result = await handler(ctx, instance_id="i-1", data=data)

        assert route.called
        assert json.loads(route.calls.last.request.content) == data
        assert result == {"id": "v-1"}

    async def test_update_vhost(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/simplehosting/instances/i-1/vhosts/site.example.com").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_simplehosting_update_vhost")
        result = await handler(ctx, instance_id="i-1", fqdn="site.example.com", data={"https": True})

        assert route.calls.last.request.method == "PATCH"
        assert result == {"ok": True}

    async def test_purge_vhost_cache(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/simplehosting/instances/i-1/vhosts/site.example.com/cache").mock(
            return_value=httpx.Response(202, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_simplehosting_purge_vhost_cache")
        result = await handler(ctx, instance_id="i-1", fqdn="site.example.com")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"ok": True}

    async def test_delete_vhost_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/simplehosting/instances/i-1/vhosts/site.example.com").mock(
            return_value=httpx.Response(204)
        )

        handler = await _get_handler(server, "gandi_simplehosting_delete_vhost")
        result = await handler(ctx, instance_id="i-1", fqdn="site.example.com")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {}

    async def test_delete_vhost_maps_404(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/simplehosting/instances/i-1/vhosts/missing.example.com").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_simplehosting_delete_vhost")
        with pytest.raises(ToolError):
            await handler(ctx, instance_id="i-1", fqdn="missing.example.com")

    @pytest.mark.parametrize(
        ("tool_name", "verb", "path", "kwargs"),
        [
            (
                "gandi_simplehosting_delete_instance",
                "delete",
                "/v5/simplehosting/instances/i-1",
                {"instance_id": "i-1"},
            ),
            (
                "gandi_simplehosting_perform_instance_action",
                "post",
                "/v5/simplehosting/instances/i-1/action",
                {"instance_id": "i-1", "data": {}},
            ),
            (
                "gandi_simplehosting_create_vhost",
                "post",
                "/v5/simplehosting/instances/i-1/vhosts",
                {"instance_id": "i-1", "data": {}},
            ),
            (
                "gandi_simplehosting_update_vhost",
                "patch",
                "/v5/simplehosting/instances/i-1/vhosts/site.example.com",
                {"instance_id": "i-1", "fqdn": "site.example.com", "data": {}},
            ),
            (
                "gandi_simplehosting_purge_vhost_cache",
                "delete",
                "/v5/simplehosting/instances/i-1/vhosts/site.example.com/cache",
                {"instance_id": "i-1", "fqdn": "site.example.com"},
            ),
        ],
    )
    async def test_write_handler_maps_error(
        self,
        ctx: AsyncMock,
        respx_mock: Any,
        server: FastMCP,
        tool_name: str,
        verb: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        getattr(respx_mock, verb)(path).mock(return_value=httpx.Response(500, json={}))

        handler = await _get_handler(server, tool_name)
        with pytest.raises(ToolError):
            await handler(ctx, **kwargs)


@pytest.mark.mocked
class TestSimpleHostingPurchases:
    async def test_create_instance(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"plan": "s+", "datacenter": "FR-SD6"}
        route = respx_mock.post("/v5/simplehosting/instances").mock(
            return_value=httpx.Response(201, json={"id": "i-9"})
        )

        handler = await _get_handler(server, "gandi_simplehosting_create_instance")
        result = await handler(ctx, data=data)

        assert route.called
        assert json.loads(route.calls.last.request.content) == data
        assert result == {"id": "i-9"}

    async def test_update_instance(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/simplehosting/instances/i-1").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_simplehosting_update_instance")
        result = await handler(ctx, instance_id="i-1", data={"plan": "m"})

        assert route.calls.last.request.method == "PATCH"
        assert result == {"ok": True}

    @pytest.mark.parametrize(
        ("tool_name", "verb", "path", "kwargs"),
        [
            ("gandi_simplehosting_create_instance", "post", "/v5/simplehosting/instances", {"data": {}}),
            (
                "gandi_simplehosting_update_instance",
                "patch",
                "/v5/simplehosting/instances/i-1",
                {"instance_id": "i-1", "data": {}},
            ),
        ],
    )
    async def test_purchase_handler_maps_error(
        self,
        ctx: AsyncMock,
        respx_mock: Any,
        server: FastMCP,
        tool_name: str,
        verb: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        getattr(respx_mock, verb)(path).mock(return_value=httpx.Response(500, json={}))

        handler = await _get_handler(server, tool_name)
        with pytest.raises(ToolError):
            await handler(ctx, **kwargs)
