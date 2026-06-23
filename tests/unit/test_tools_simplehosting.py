"""Behavioural tests for the Simple Hosting tool handlers.

Each handler is a closure registered on a FastMCP server. We register the
tools on a bare server, pull the underlying coroutine via ``tool.fn``, and
drive it with a fake ``Context`` whose lifespan carries a mocked ``GandiClient``.

Three behaviours are pinned per tier:

* happy path — the handler forwards to the right client method and returns its
  payload verbatim;
* gating — write tools refuse in read-only mode, purchase tools refuse without
  ``GANDI_ALLOW_PURCHASES``, both surfaced as ``ToolError``;
* error mapping — a client exception is translated to ``ToolError`` rather than
  leaking the raw Gandi exception.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from gandi_mcp.errors import GandiNotFoundError
from gandi_mcp.tools.simplehosting import register_simplehosting_tools
from tests.conftest import build_fake_ctx

if TYPE_CHECKING:
    from gandi_mcp.config import GandiConfig

pytestmark = pytest.mark.asyncio

INSTANCE_ID = "11111111-2222-3333-4444-555555555555"
FQDN = "shop.example.com"


@pytest.fixture
def server() -> FastMCP:
    """A bare server with every Simple Hosting tool registered."""
    mcp = FastMCP(name="test-simplehosting")
    register_simplehosting_tools(mcp)
    return mcp


async def _fn(server: FastMCP, name: str) -> Any:
    """Return the underlying coroutine function for a registered tool."""
    tool = await server.get_tool(name)
    return tool.fn


def _ctx(config: GandiConfig, client: Any) -> Any:
    return build_fake_ctx(config, client=client)


@pytest.fixture
def readonly_ctx(readonly_config: GandiConfig) -> Any:
    return _ctx(readonly_config, AsyncMock())


@pytest.fixture
def readwrite_ctx(readwrite_config: GandiConfig) -> Any:
    return _ctx(readwrite_config, AsyncMock())


@pytest.fixture
def full_ctx(readwrite_with_purchases_config: GandiConfig) -> Any:
    return _ctx(readwrite_with_purchases_config, AsyncMock())


class TestReadTools:
    async def test_list_instances(self, server: FastMCP, readonly_ctx: Any) -> None:
        readonly_ctx.lifespan_context.client.simplehosting_list_instances.return_value = [{"id": INSTANCE_ID}]
        fn = await _fn(server, "gandi_simplehosting_list_instances")
        result = await fn(readonly_ctx)
        assert result == [{"id": INSTANCE_ID}]
        readonly_ctx.lifespan_context.client.simplehosting_list_instances.assert_awaited_once_with()

    async def test_get_instance(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        client.simplehosting_get_instance.return_value = {"id": INSTANCE_ID}
        fn = await _fn(server, "gandi_simplehosting_get_instance")
        result = await fn(readonly_ctx, INSTANCE_ID)
        assert result == {"id": INSTANCE_ID}
        client.simplehosting_get_instance.assert_awaited_once_with(INSTANCE_ID)

    async def test_list_vhosts(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        client.simplehosting_list_vhosts.return_value = [{"fqdn": FQDN}]
        fn = await _fn(server, "gandi_simplehosting_list_vhosts")
        result = await fn(readonly_ctx, INSTANCE_ID)
        assert result == [{"fqdn": FQDN}]
        client.simplehosting_list_vhosts.assert_awaited_once_with(INSTANCE_ID)

    async def test_get_vhost(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        client.simplehosting_get_vhost.return_value = {"fqdn": FQDN}
        fn = await _fn(server, "gandi_simplehosting_get_vhost")
        result = await fn(readonly_ctx, INSTANCE_ID, FQDN)
        assert result == {"fqdn": FQDN}
        client.simplehosting_get_vhost.assert_awaited_once_with(INSTANCE_ID, FQDN)

    async def test_get_instance_usage(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        client.simplehosting_get_instance_usage.return_value = {"cpu": 0.5}
        fn = await _fn(server, "gandi_simplehosting_get_instance_usage")
        result = await fn(readonly_ctx, INSTANCE_ID)
        assert result == {"cpu": 0.5}
        client.simplehosting_get_instance_usage.assert_awaited_once_with(INSTANCE_ID)

    async def test_read_tool_maps_client_error(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        client.simplehosting_get_instance.side_effect = GandiNotFoundError("no such instance")
        fn = await _fn(server, "gandi_simplehosting_get_instance")
        with pytest.raises(ToolError, match="Resource not found"):
            await fn(readonly_ctx, INSTANCE_ID)


class TestWriteTools:
    async def test_delete_instance_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        client.simplehosting_delete_instance.return_value = {}
        fn = await _fn(server, "gandi_simplehosting_delete_instance")
        result = await fn(readwrite_ctx, INSTANCE_ID)
        assert result == {}
        client.simplehosting_delete_instance.assert_awaited_once_with(INSTANCE_ID)

    async def test_perform_instance_action_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        payload = {"action": "restart"}
        client.simplehosting_instance_action.return_value = {"status": "ok"}
        fn = await _fn(server, "gandi_simplehosting_perform_instance_action")
        result = await fn(readwrite_ctx, INSTANCE_ID, payload)
        assert result == {"status": "ok"}
        client.simplehosting_instance_action.assert_awaited_once_with(INSTANCE_ID, payload)

    async def test_create_vhost_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        payload = {"fqdn": FQDN}
        client.simplehosting_create_vhost.return_value = {"id": "vh1"}
        fn = await _fn(server, "gandi_simplehosting_create_vhost")
        result = await fn(readwrite_ctx, INSTANCE_ID, payload)
        assert result == {"id": "vh1"}
        client.simplehosting_create_vhost.assert_awaited_once_with(INSTANCE_ID, payload)

    async def test_delete_vhost_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        client.simplehosting_delete_vhost.return_value = {}
        fn = await _fn(server, "gandi_simplehosting_delete_vhost")
        result = await fn(readwrite_ctx, INSTANCE_ID, FQDN)
        assert result == {}
        client.simplehosting_delete_vhost.assert_awaited_once_with(INSTANCE_ID, FQDN)

    async def test_update_vhost_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        payload = {"https_strict": True}
        client.simplehosting_update_vhost.return_value = {"fqdn": FQDN}
        fn = await _fn(server, "gandi_simplehosting_update_vhost")
        result = await fn(readwrite_ctx, INSTANCE_ID, FQDN, payload)
        assert result == {"fqdn": FQDN}
        client.simplehosting_update_vhost.assert_awaited_once_with(INSTANCE_ID, FQDN, payload)

    async def test_purge_vhost_cache_happy_path(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        client.simplehosting_purge_vhost_cache.return_value = {}
        fn = await _fn(server, "gandi_simplehosting_purge_vhost_cache")
        result = await fn(readwrite_ctx, INSTANCE_ID, FQDN)
        assert result == {}
        client.simplehosting_purge_vhost_cache.assert_awaited_once_with(INSTANCE_ID, FQDN)

    @pytest.mark.parametrize(
        ("tool_name", "args"),
        [
            ("gandi_simplehosting_delete_instance", (INSTANCE_ID,)),
            ("gandi_simplehosting_perform_instance_action", (INSTANCE_ID, {})),
            ("gandi_simplehosting_create_vhost", (INSTANCE_ID, {})),
            ("gandi_simplehosting_delete_vhost", (INSTANCE_ID, FQDN)),
            ("gandi_simplehosting_update_vhost", (INSTANCE_ID, FQDN, {})),
            ("gandi_simplehosting_purge_vhost_cache", (INSTANCE_ID, FQDN)),
        ],
    )
    async def test_write_tool_blocked_in_readonly(
        self, server: FastMCP, readonly_ctx: Any, tool_name: str, args: tuple[Any, ...]
    ) -> None:
        fn = await _fn(server, tool_name)
        with pytest.raises(ToolError, match="read-only mode"):
            await fn(readonly_ctx, *args)

    async def test_write_tool_does_not_touch_client_when_blocked(self, server: FastMCP, readonly_ctx: Any) -> None:
        client = readonly_ctx.lifespan_context.client
        fn = await _fn(server, "gandi_simplehosting_delete_instance")
        with pytest.raises(ToolError):
            await fn(readonly_ctx, INSTANCE_ID)
        client.simplehosting_delete_instance.assert_not_awaited()

    async def test_write_tool_maps_client_error(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        client.simplehosting_delete_vhost.side_effect = GandiNotFoundError("no such vhost")
        fn = await _fn(server, "gandi_simplehosting_delete_vhost")
        with pytest.raises(ToolError, match="Resource not found"):
            await fn(readwrite_ctx, INSTANCE_ID, FQDN)


class TestPurchaseTools:
    async def test_create_instance_happy_path(self, server: FastMCP, full_ctx: Any) -> None:
        client = full_ctx.lifespan_context.client
        payload = {"plan": "small"}
        client.simplehosting_create_instance.return_value = {"id": INSTANCE_ID}
        fn = await _fn(server, "gandi_simplehosting_create_instance")
        result = await fn(full_ctx, payload)
        assert result == {"id": INSTANCE_ID}
        client.simplehosting_create_instance.assert_awaited_once_with(payload)

    async def test_update_instance_happy_path(self, server: FastMCP, full_ctx: Any) -> None:
        client = full_ctx.lifespan_context.client
        payload = {"plan": "large"}
        client.simplehosting_update_instance.return_value = {"id": INSTANCE_ID}
        fn = await _fn(server, "gandi_simplehosting_update_instance")
        result = await fn(full_ctx, INSTANCE_ID, payload)
        assert result == {"id": INSTANCE_ID}
        client.simplehosting_update_instance.assert_awaited_once_with(INSTANCE_ID, payload)

    @pytest.mark.parametrize(
        ("tool_name", "args"),
        [
            ("gandi_simplehosting_create_instance", ({},)),
            ("gandi_simplehosting_update_instance", (INSTANCE_ID, {})),
        ],
    )
    async def test_purchase_tool_blocked_in_readonly(
        self, server: FastMCP, readonly_ctx: Any, tool_name: str, args: tuple[Any, ...]
    ) -> None:
        """Read-only loses the narrower write check first, before the purchase check."""
        fn = await _fn(server, tool_name)
        with pytest.raises(ToolError, match="read-only mode"):
            await fn(readonly_ctx, *args)

    @pytest.mark.parametrize(
        ("tool_name", "args"),
        [
            ("gandi_simplehosting_create_instance", ({},)),
            ("gandi_simplehosting_update_instance", (INSTANCE_ID, {})),
        ],
    )
    async def test_purchase_tool_blocked_without_purchases(
        self, server: FastMCP, readwrite_ctx: Any, tool_name: str, args: tuple[Any, ...]
    ) -> None:
        fn = await _fn(server, tool_name)
        with pytest.raises(ToolError, match="purchases are disabled"):
            await fn(readwrite_ctx, *args)

    async def test_purchase_tool_does_not_touch_client_when_blocked(self, server: FastMCP, readwrite_ctx: Any) -> None:
        client = readwrite_ctx.lifespan_context.client
        fn = await _fn(server, "gandi_simplehosting_create_instance")
        with pytest.raises(ToolError):
            await fn(readwrite_ctx, {})
        client.simplehosting_create_instance.assert_not_awaited()

    async def test_purchase_tool_maps_client_error(self, server: FastMCP, full_ctx: Any) -> None:
        client = full_ctx.lifespan_context.client
        client.simplehosting_update_instance.side_effect = GandiNotFoundError("no such instance")
        fn = await _fn(server, "gandi_simplehosting_update_instance")
        with pytest.raises(ToolError, match="Resource not found"):
            await fn(full_ctx, INSTANCE_ID, {})
