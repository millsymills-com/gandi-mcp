"""Handler-level tests for the linked-zone tools (/v5/linkedzone).

Each tool is a thin closure registered on a FastMCP server; the bodies wrap a
single ``GandiClient`` call, gate writes behind ``assert_readwrite``, and funnel
failures through ``handle_client_error``. These tests drive the *registered*
handlers (via ``tool.fn``) against a real ``GandiClient`` with respx-mocked HTTP,
so the assertions are about behaviour an agent would observe:

* read tools return the Gandi payload in readonly mode;
* write tools refuse to run in readonly mode (``GandiReadOnlyError``) and pass
  the payload through in readwrite mode;
* an upstream API error surfaces as a ``ToolError``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
import respx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from gandi_mcp.clients.gandi import GandiClient
from gandi_mcp.config import GandiConfig, GandiMode
from gandi_mcp.errors import GandiReadOnlyError
from gandi_mcp.server import ServerContext
from gandi_mcp.tools.linkedzone import register_linkedzone_tools

BASE_URL = "https://api.gandi.net"


def _config(mode: GandiMode) -> GandiConfig:
    return GandiConfig(_env_file=None, gandi_token="t", gandi_mode=mode)


def _ctx(client: GandiClient, mode: GandiMode) -> Any:
    """Fake Context exposing ``lifespan_context`` with a live client + config."""
    ctx = MagicMock()
    ctx.lifespan_context = ServerContext(config=_config(mode), client=client)
    return ctx


@pytest.fixture
async def client() -> Any:
    c = GandiClient(base_url=BASE_URL, token="t", max_retries=1)
    yield c
    await c.close()


@pytest.fixture
async def handlers() -> dict[str, Any]:
    """Map of tool name -> raw handler function for the registered tools."""
    mcp = FastMCP("test")
    register_linkedzone_tools(mcp)
    return {tool.name: tool.fn for tool in await mcp.list_tools()}


# Every linked-zone tool, with the HTTP method/path it hits and the extra
# keyword args the handler takes beyond ``ctx``. ``write`` marks tools gated by
# ``assert_readwrite``.
READ_CASES = [
    ("gandi_linkedzone_list_domains", "GET", "/v5/linkedzone/domains", {}),
    ("gandi_linkedzone_get_domain", "GET", "/v5/linkedzone/domains/example.com", {"domain": "example.com"}),
    ("gandi_linkedzone_list_zones", "GET", "/v5/linkedzone/zones", {}),
    ("gandi_linkedzone_get_zone", "GET", "/v5/linkedzone/zones/z1", {"zone_id": "z1"}),
    ("gandi_linkedzone_list_tasks", "GET", "/v5/linkedzone/tasks", {}),
    ("gandi_linkedzone_get_task", "GET", "/v5/linkedzone/tasks/t1", {"task_id": "t1"}),
]

WRITE_CASES = [
    ("gandi_linkedzone_create_zone", "POST", "/v5/linkedzone/zones", {"data": {"name": "z"}}),
    ("gandi_linkedzone_attach_domain", "POST", "/v5/linkedzone/zones/z1", {"zone_id": "z1", "data": {"fqdn": "x"}}),
    ("gandi_linkedzone_update_zone", "PATCH", "/v5/linkedzone/zones/z1", {"zone_id": "z1", "data": {"name": "n"}}),
    ("gandi_linkedzone_delete_zone", "DELETE", "/v5/linkedzone/zones/z1", {"zone_id": "z1"}),
    (
        "gandi_linkedzone_link_domains",
        "PATCH",
        "/v5/linkedzone/zones/z1/link/domains",
        {"zone_id": "z1", "data": {"domains": ["x"]}},
    ),
    ("gandi_linkedzone_unlink_domains", "PATCH", "/v5/linkedzone/unlink/domains", {"data": {"domains": ["x"]}}),
]


def _route(mock: respx.MockRouter, method: str, path: str) -> Any:
    return getattr(mock, method.lower())(path)


class TestReadHandlers:
    @pytest.mark.parametrize(("name", "method", "path", "kwargs"), READ_CASES)
    async def test_happy_path_returns_payload(
        self,
        client: GandiClient,
        handlers: dict[str, Any],
        name: str,
        method: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        payload = {"ok": True} if "list" not in name else [{"ok": True}]
        with respx.mock(base_url=BASE_URL) as mock:
            _route(mock, method, path).mock(return_value=httpx.Response(200, json=payload))
            result = await handlers[name](_ctx(client, GandiMode.READONLY), **kwargs)
        assert result == payload

    @pytest.mark.parametrize(("name", "method", "path", "kwargs"), READ_CASES)
    async def test_api_error_surfaces_as_tool_error(
        self,
        client: GandiClient,
        handlers: dict[str, Any],
        name: str,
        method: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        with respx.mock(base_url=BASE_URL) as mock:
            _route(mock, method, path).mock(return_value=httpx.Response(404, json={"message": "nope"}))
            with pytest.raises(ToolError, match="not found"):
                await handlers[name](_ctx(client, GandiMode.READONLY), **kwargs)


class TestWriteHandlers:
    @pytest.mark.parametrize(("name", "method", "path", "kwargs"), WRITE_CASES)
    async def test_happy_path_passes_payload_through(
        self,
        client: GandiClient,
        handlers: dict[str, Any],
        name: str,
        method: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        with respx.mock(base_url=BASE_URL) as mock:
            route = _route(mock, method, path).mock(return_value=httpx.Response(200, json={"id": "z1"}))
            result = await handlers[name](_ctx(client, GandiMode.READWRITE), **kwargs)
        assert result == {"id": "z1"}
        assert route.called

    @pytest.mark.parametrize(("name", "kwargs"), [(c[0], c[3]) for c in WRITE_CASES])
    async def test_readonly_mode_blocks_write(
        self,
        client: GandiClient,
        handlers: dict[str, Any],
        name: str,
        kwargs: dict[str, Any],
    ) -> None:
        # assert_readwrite must fire before any HTTP call; no respx route is
        # registered so an accidental request would also fail loudly.
        with pytest.raises((GandiReadOnlyError, ToolError), match="read-only"):
            await handlers[name](_ctx(client, GandiMode.READONLY), **kwargs)

    @pytest.mark.parametrize(("name", "method", "path", "kwargs"), WRITE_CASES)
    async def test_api_error_surfaces_as_tool_error(
        self,
        client: GandiClient,
        handlers: dict[str, Any],
        name: str,
        method: str,
        path: str,
        kwargs: dict[str, Any],
    ) -> None:
        with respx.mock(base_url=BASE_URL) as mock:
            _route(mock, method, path).mock(return_value=httpx.Response(409, json={"message": "busy"}))
            with pytest.raises(ToolError, match="conflict"):
                await handlers[name](_ctx(client, GandiMode.READWRITE), **kwargs)
