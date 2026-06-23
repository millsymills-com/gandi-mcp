"""Mocked-integration tests for the mailbox area tools.

Covers the read surface (domains, mailboxes, forwards, slots, quotas,
products), the free-write surface (validate domain, mailbox update/delete,
forward create/update/delete), and the gated purchase surface (mailbox
create/renew, buy product). Request shape, `_seg` URL-encoding, the 204 No
Content contract, and error mapping are asserted; gating itself lives in the
safety-gate tests. Cassette recording is deferred to #102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.mailbox import (
    register_mailbox_purchase_tools,
    register_mailbox_read_tools,
    register_mailbox_write_tools,
)

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
    register_mailbox_read_tools(s)
    register_mailbox_write_tools(s)
    register_mailbox_purchase_tools(s)
    return s


@pytest.mark.mocked
class TestMailboxReads:
    async def test_list_mailboxes(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = [{"address": "a@example.com"}]
        route = respx_mock.get("/v5/mailbox/mailboxes").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_mailbox_list_mailboxes")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_mailbox_url_encodes_email(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.get("/v5/mailbox/mailboxes/a%40example.com").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(server, "gandi_mailbox_get_mailbox")
        await handler(ctx, email="a@example.com")

        assert route.calls.last.request.url.raw_path == b"/v5/mailbox/mailboxes/a%40example.com"

    async def test_get_quotas(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"used": 1, "total": 5}
        route = respx_mock.get("/v5/mailbox/quotas").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_mailbox_get_quotas")
        result = await handler(ctx)

        assert route.called
        assert result == payload

    async def test_get_slot(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"id": "slot-1"}
        route = respx_mock.get("/v5/mailbox/slots/slot-1").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(server, "gandi_mailbox_get_slot")
        result = await handler(ctx, slot_id="slot-1")

        assert route.called
        assert result == payload

    async def test_get_mailbox_maps_404(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.get("/v5/mailbox/mailboxes/missing%40example.com").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_mailbox_get_mailbox")
        with pytest.raises(ToolError):
            await handler(ctx, email="missing@example.com")


@pytest.mark.mocked
class TestMailboxWrites:
    async def test_validate_domain(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"check": "dns"}
        route = respx_mock.post("/v5/mailbox/domains/example.com/validate").mock(
            return_value=httpx.Response(200, json={"valid": True})
        )

        handler = await _get_handler(server, "gandi_mailbox_validate_domain")
        result = await handler(ctx, domain="example.com", data=data)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == data
        assert result == {"valid": True}

    async def test_update_mailbox(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.patch("/v5/mailbox/mailboxes/a%40example.com").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_mailbox_update_mailbox")
        result = await handler(ctx, email="a@example.com", data={"aliases": ["x"]})

        assert route.calls.last.request.method == "PATCH"
        assert result == {"ok": True}

    async def test_delete_mailbox_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/mailbox/mailboxes/a%40example.com").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_mailbox_delete_mailbox")
        result = await handler(ctx, email="a@example.com")

        assert result == {}

    async def test_create_forward(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"source": "a@example.com", "destinations": ["b@example.com"]}
        route = respx_mock.post("/v5/mailbox/forwards").mock(return_value=httpx.Response(201, json={"id": "f-1"}))

        handler = await _get_handler(server, "gandi_mailbox_create_forward")
        result = await handler(ctx, data=data)

        assert route.called
        assert json.loads(route.calls.last.request.content) == data
        assert result == {"id": "f-1"}

    async def test_update_forward(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.put("/v5/mailbox/forwards/a%40example.com").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_mailbox_update_forward")
        result = await handler(ctx, source="a@example.com", data={"destinations": ["c@example.com"]})

        assert route.calls.last.request.method == "PUT"
        assert route.calls.last.request.url.raw_path == b"/v5/mailbox/forwards/a%40example.com"
        assert result == {"ok": True}

    async def test_delete_forward(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/mailbox/forwards/a%40example.com").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_mailbox_delete_forward")
        result = await handler(ctx, source="a@example.com")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"ok": True}


@pytest.mark.mocked
class TestMailboxPurchases:
    async def test_create_mailbox(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"address": "new@example.com", "password": "x"}
        route = respx_mock.post("/v5/mailbox/mailboxes").mock(return_value=httpx.Response(201, json={"id": "m-9"}))

        handler = await _get_handler(server, "gandi_mailbox_create_mailbox")
        result = await handler(ctx, data=data)

        assert route.called
        assert json.loads(route.calls.last.request.content) == data
        assert result == {"id": "m-9"}

    async def test_renew_mailbox(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/mailbox/mailboxes/a%40example.com/renew").mock(
            return_value=httpx.Response(202, json={"ok": True})
        )

        handler = await _get_handler(server, "gandi_mailbox_renew_mailbox")
        result = await handler(ctx, email="a@example.com", data={"duration": 1})

        assert route.called
        assert route.calls.last.request.method == "POST"
        assert result == {"ok": True}

    async def test_buy_product(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        data = {"product": "standard", "quantity": 1}
        route = respx_mock.post("/v5/mailbox/products").mock(return_value=httpx.Response(201, json={"id": "p-1"}))

        handler = await _get_handler(server, "gandi_mailbox_buy_product")
        result = await handler(ctx, data=data)

        assert route.called
        assert json.loads(route.calls.last.request.content) == data
        assert result == {"id": "p-1"}
