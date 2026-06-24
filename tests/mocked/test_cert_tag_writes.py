"""Mocked-integration tests for the certificate tag write tools.

Covers add (POST), replace (PUT), update (PATCH), and delete (DELETE) of the
operator-defined tags on an issued certificate. Request shape, `_seg`
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

from gandi_mcp.tools.certificate import register_certificate_write_tools

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
    register_certificate_write_tools(s)
    return s


@pytest.mark.mocked
class TestCertAddTag:
    async def test_posts_name_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tag created"}
        route = respx_mock.post("/v5/certificate/issued-certs/cert-1/tags").mock(
            return_value=httpx.Response(201, json=payload)
        )

        handler = await _get_handler(server, "gandi_cert_add_tag")
        result = await handler(ctx, cert_id="cert-1", name="prod")

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == {"name": "prod"}
        assert result == payload

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.post("/v5/certificate/issued-certs/a%2Fb/tags").mock(
            return_value=httpx.Response(201, json={})
        )

        handler = await _get_handler(server, "gandi_cert_add_tag")
        await handler(ctx, cert_id="a/b", name="prod")

        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb/tags"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.post("/v5/certificate/issued-certs/missing/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_cert_add_tag")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing", name="prod")


@pytest.mark.mocked
class TestCertReplaceTags:
    async def test_puts_tags_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tags replaced"}
        route = respx_mock.put("/v5/certificate/issued-certs/cert-1/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_cert_replace_tags")
        result = await handler(ctx, cert_id="cert-1", tags=["prod", "billing"])

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"tags": ["prod", "billing"]}
        assert result == payload

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/certificate/issued-certs/cert-1/tags").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_cert_replace_tags")
        result = await handler(ctx, cert_id="cert-1", tags=["prod"])

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.put("/v5/certificate/issued-certs/missing/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_cert_replace_tags")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing", tags=["prod"])


@pytest.mark.mocked
class TestCertUpdateTags:
    async def test_patches_tags_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        payload = {"message": "Tags added"}
        route = respx_mock.patch("/v5/certificate/issued-certs/cert-1/tags").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(server, "gandi_cert_update_tags")
        result = await handler(ctx, cert_id="cert-1", tags=["staging"])

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"tags": ["staging"]}
        assert result == payload

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/certificate/issued-certs/cert-1/tags").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_cert_update_tags")
        result = await handler(ctx, cert_id="cert-1", tags=["staging"])

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.patch("/v5/certificate/issued-certs/missing/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_cert_update_tags")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing", tags=["staging"])


@pytest.mark.mocked
class TestCertDeleteTags:
    async def test_deletes_and_returns_payload(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        route = respx_mock.delete("/v5/certificate/issued-certs/cert-1/tags").mock(
            return_value=httpx.Response(200, json={"message": "Tags removed"})
        )

        handler = await _get_handler(server, "gandi_cert_delete_tags")
        result = await handler(ctx, cert_id="cert-1")

        assert route.called
        assert route.calls.last.request.method == "DELETE"
        assert result == {"message": "Tags removed"}

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/certificate/issued-certs/cert-1/tags").mock(return_value=httpx.Response(204))

        handler = await _get_handler(server, "gandi_cert_delete_tags")
        result = await handler(ctx, cert_id="cert-1")

        assert result == {}

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, server: FastMCP) -> None:
        respx_mock.delete("/v5/certificate/issued-certs/missing/tags").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(server, "gandi_cert_delete_tags")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing")
