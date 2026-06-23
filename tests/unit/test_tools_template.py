"""Behavioural tests for the template tool handlers (/v5/template).

The schema-matrix test pins the *shape* of these tools statically; this module
exercises their *handler bodies* end-to-end. Each test pulls the live handler
off the FastMCP server (``tool.fn``), hands it a Context whose lifespan carries
a real :class:`GandiClient` backed by respx, and asserts the observable
behaviour: the right HTTP call goes out, the payload passes through, the write
gate blocks in read-only mode, and a client error surfaces as a ``ToolError``.
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
from gandi_mcp.server import ServerContext, create_server
from gandi_mcp.tools.template import register_template_tools

BASE_URL = "https://api.gandi.net"


def _config(mode: GandiMode) -> GandiConfig:
    return GandiConfig(_env_file=None, gandi_token="t", gandi_mode=mode)


def _ctx(config: GandiConfig, client: GandiClient | None) -> Any:
    ctx = MagicMock()
    ctx.lifespan_context = ServerContext(config=config, client=client)
    return ctx


async def _handler(name: str):  # type: ignore[no-untyped-def]
    """Return the raw async handler registered under ``name``."""
    server = create_server(_config(GandiMode.READWRITE))
    tool = await server.get_tool(name)
    return tool.fn


@pytest.fixture
def client() -> GandiClient:
    return GandiClient(base_url=BASE_URL, token="t", max_retries=1)


@pytest.fixture
def readwrite_ctx(client: GandiClient) -> Any:
    return _ctx(_config(GandiMode.READWRITE), client)


@pytest.fixture
def readonly_ctx(client: GandiClient) -> Any:
    return _ctx(_config(GandiMode.READONLY), client)


class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_template_tools_registers_read_and_write(self) -> None:
        mcp = FastMCP("test")
        register_template_tools(mcp)
        names = {t.name for t in await mcp.list_tools()}
        assert {
            "gandi_template_list_templates",
            "gandi_template_get_template",
            "gandi_template_get_dispatch",
            "gandi_template_create_template",
            "gandi_template_update_template",
            "gandi_template_apply_template",
        } <= names


class TestReadHandlers:
    @pytest.mark.asyncio
    async def test_list_templates(self, readwrite_ctx: Any) -> None:
        payload = [{"id": "tpl-1"}, {"id": "tpl-2"}]
        fn = await _handler("gandi_template_list_templates")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.get("/v5/template/templates").mock(
                return_value=httpx.Response(200, json=payload),
            )
            result = await fn(readwrite_ctx)
        assert route.called
        assert result == payload

    @pytest.mark.asyncio
    async def test_get_template(self, readwrite_ctx: Any) -> None:
        payload = {"id": "tpl-1", "name": "web"}
        fn = await _handler("gandi_template_get_template")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.get("/v5/template/templates/tpl-1").mock(
                return_value=httpx.Response(200, json=payload),
            )
            result = await fn(readwrite_ctx, "tpl-1")
        assert route.called
        assert result == payload

    @pytest.mark.asyncio
    async def test_get_dispatch(self, readwrite_ctx: Any) -> None:
        payload = {"id": "disp-9", "status": "done"}
        fn = await _handler("gandi_template_get_dispatch")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.get("/v5/template/dispatch/disp-9").mock(
                return_value=httpx.Response(200, json=payload),
            )
            result = await fn(readwrite_ctx, "disp-9")
        assert route.called
        assert result == payload

    @pytest.mark.asyncio
    async def test_get_template_not_found_surfaces_tool_error(self, readwrite_ctx: Any) -> None:
        fn = await _handler("gandi_template_get_template")
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/template/templates/missing").mock(
                return_value=httpx.Response(404, json={"message": "not found"}),
            )
            with pytest.raises(ToolError, match="Resource not found"):
                await fn(readwrite_ctx, "missing")

    @pytest.mark.asyncio
    async def test_list_templates_server_error_surfaces_tool_error(self, readwrite_ctx: Any) -> None:
        fn = await _handler("gandi_template_list_templates")
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/template/templates").mock(
                return_value=httpx.Response(500, json={"message": "boom"}),
            )
            with pytest.raises(ToolError, match="Gandi server error"):
                await fn(readwrite_ctx)

    @pytest.mark.asyncio
    async def test_get_dispatch_not_found_surfaces_tool_error(self, readwrite_ctx: Any) -> None:
        fn = await _handler("gandi_template_get_dispatch")
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/template/dispatch/missing").mock(
                return_value=httpx.Response(404, json={"message": "not found"}),
            )
            with pytest.raises(ToolError, match="Resource not found"):
                await fn(readwrite_ctx, "missing")


class TestWriteHandlersHappyPath:
    @pytest.mark.asyncio
    async def test_create_template(self, readwrite_ctx: Any) -> None:
        data = {"name": "web", "payload": {}}
        fn = await _handler("gandi_template_create_template")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.post("/v5/template/templates").mock(
                return_value=httpx.Response(201, json={"id": "tpl-new"}),
            )
            result = await fn(readwrite_ctx, data)
        assert route.called
        assert (
            route.calls.last.request.read()
            == httpx.Request("POST", f"{BASE_URL}/v5/template/templates", json=data).read()
        )
        assert result == {"id": "tpl-new"}

    @pytest.mark.asyncio
    async def test_update_template(self, readwrite_ctx: Any) -> None:
        data = {"name": "renamed"}
        fn = await _handler("gandi_template_update_template")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.patch("/v5/template/templates/tpl-1").mock(
                return_value=httpx.Response(200, json={"id": "tpl-1"}),
            )
            result = await fn(readwrite_ctx, "tpl-1", data)
        assert route.called
        assert result == {"id": "tpl-1"}

    @pytest.mark.asyncio
    async def test_apply_template(self, readwrite_ctx: Any) -> None:
        data = {"domains": ["example.com"]}
        fn = await _handler("gandi_template_apply_template")
        with respx.mock(base_url=BASE_URL) as mock:
            route = mock.post("/v5/template/templates/tpl-1").mock(
                return_value=httpx.Response(202, json={"dispatch_id": "disp-1"}),
            )
            result = await fn(readwrite_ctx, "tpl-1", data)
        assert route.called
        assert result == {"dispatch_id": "disp-1"}


class TestWriteGate:
    """Read-only mode must block every write handler before any HTTP call.

    No routes are registered: the gate must raise before any request is made,
    so respx is armed only to fail loudly if the handler tries to reach out.
    """

    @pytest.mark.asyncio
    async def test_create_template_blocked(self, readonly_ctx: Any) -> None:
        fn = await _handler("gandi_template_create_template")
        with respx.mock(base_url=BASE_URL), pytest.raises(ToolError, match="read-only mode"):
            await fn(readonly_ctx, {"name": "web"})

    @pytest.mark.asyncio
    async def test_update_template_blocked(self, readonly_ctx: Any) -> None:
        fn = await _handler("gandi_template_update_template")
        with respx.mock(base_url=BASE_URL), pytest.raises(ToolError, match="read-only mode"):
            await fn(readonly_ctx, "tpl-1", {"name": "x"})

    @pytest.mark.asyncio
    async def test_apply_template_blocked(self, readonly_ctx: Any) -> None:
        fn = await _handler("gandi_template_apply_template")
        with respx.mock(base_url=BASE_URL), pytest.raises(ToolError, match="read-only mode"):
            await fn(readonly_ctx, "tpl-1", {"domains": []})
