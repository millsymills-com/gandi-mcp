"""Mocked-integration tests for the LiveDNS record sub-resource write tools.

Covers the per-name and per-(name, type) record mutation endpoints:
create/replace/delete under a name, and create/update at a specific type.
Request shape, `_seg` URL-encoding, the 204 No Content contract, and error
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
class TestCreateNamedRecord:
    async def test_posts_body_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Created"}
        route = respx_mock.post("/v5/livedns/domains/example.com/records/www").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_create_named_record")
        result = await handler(ctx, fqdn="example.com", name="www", rrset_type="A", values=["1.2.3.4"], ttl=300)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"rrset_type": "A", "rrset_values": ["1.2.3.4"], "rrset_ttl": 300}
        assert result == payload

    async def test_omits_ttl_when_not_given(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/livedns/domains/example.com/records/www").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_create_named_record")
        await handler(ctx, fqdn="example.com", name="www", rrset_type="A", values=["1.2.3.4"])

        assert json.loads(route.calls.last.request.content) == {"rrset_type": "A", "rrset_values": ["1.2.3.4"]}

    async def test_url_encodes_name(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/livedns/domains/example.com/records/a%2Fb").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_create_named_record")
        await handler(ctx, fqdn="example.com", name="a/b", rrset_type="A", values=["1.2.3.4"])

        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/records/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/livedns/domains/missing.com/records/www").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_livedns_create_named_record")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="missing.com", name="www", rrset_type="A", values=["1.2.3.4"])


@pytest.mark.mocked
class TestReplaceNamedRecords:
    async def test_puts_items_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        items = [{"rrset_type": "A", "rrset_values": ["1.2.3.4"]}]
        payload = {"message": "Replaced"}
        route = respx_mock.put("/v5/livedns/domains/example.com/records/www").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_replace_named_records")
        result = await handler(ctx, fqdn="example.com", name="www", items=items)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"items": items}
        assert result == payload

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/livedns/domains/example.com/records/www").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_livedns_replace_named_records")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", name="www", items=[])


@pytest.mark.mocked
class TestDeleteNamedRecords:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/livedns/domains/example.com/records/www").mock(
            return_value=httpx.Response(200, json={"message": "Deleted"})
        )

        handler = await _get_handler(server, "gandi_livedns_delete_named_records")
        result = await handler(ctx, fqdn="example.com", name="www")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "Deleted"}

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/livedns/domains/example.com/records/www").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_livedns_delete_named_records")
        result = await handler(ctx, fqdn="example.com", name="www")

        assert result == {}

    async def test_url_encodes_name(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/livedns/domains/example.com/records/a%2Fb").mock(
            return_value=httpx.Response(204)
        )

        handler = await _get_handler(server, "gandi_livedns_delete_named_records")
        await handler(ctx, fqdn="example.com", name="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/records/a%2Fb"


@pytest.mark.mocked
class TestCreateTypedRecord:
    async def test_posts_body_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Created"}
        route = respx_mock.post("/v5/livedns/domains/example.com/records/www/A").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_create_typed_record")
        result = await handler(ctx, fqdn="example.com", name="www", rrset_type="A", values=["1.2.3.4"], ttl=600)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"rrset_values": ["1.2.3.4"], "rrset_ttl": 600}
        assert result == payload

    async def test_url_encodes_name_and_type(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/livedns/domains/example.com/records/a%2Fb/A").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_create_typed_record")
        await handler(ctx, fqdn="example.com", name="a/b", rrset_type="A", values=["1.2.3.4"])

        assert route.calls.last.request.url.raw_path == b"/v5/livedns/domains/example.com/records/a%2Fb/A"


@pytest.mark.mocked
class TestUpdateRecord:
    async def test_patches_body_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Updated"}
        route = respx_mock.patch("/v5/livedns/domains/example.com/records/www/A").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_livedns_update_record")
        result = await handler(ctx, fqdn="example.com", name="www", rrset_type="A", values=["5.6.7.8"])

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"rrset_values": ["5.6.7.8"]}
        assert result == payload

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/livedns/domains/example.com/records/www/A").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(server, "gandi_livedns_update_record")
        with pytest.raises(ToolError):
            await handler(ctx, fqdn="example.com", name="www", rrset_type="A", values=["5.6.7.8"])
