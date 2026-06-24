"""Mocked-integration tests for certificate DCV, CRT fetch, and update tools.

Covers the issue #165 surface: DCV parameter computation (POST), DCV resend
(PUT) / method change (PATCH), raw CRT fetch (GET text/plain), and certificate
update (PATCH). Request shape, ``_seg`` URL-encoding, the 204 No Content
contract, the raw (non-JSON) CRT body, and error mapping are asserted; gating
lives in the safety-gate tests. Cassette recording is deferred.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.function_tool import FunctionTool

from gandi_mcp.tools.certificate import (
    register_certificate_read_tools,
    register_certificate_write_tools,
)

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


async def _get_handler(server: FastMCP, name: str) -> Any:
    tool = await server.get_tool(name)
    assert tool is not None, f"tool {name!r} not registered"
    assert isinstance(tool, FunctionTool), f"tool {name!r} is not a FunctionTool"
    return tool.fn


@pytest.fixture
def read_server() -> FastMCP:
    s = FastMCP(name="t")
    register_certificate_read_tools(s)
    return s


@pytest.fixture
def write_server() -> FastMCP:
    s = FastMCP(name="t")
    register_certificate_write_tools(s)
    return s


@pytest.mark.mocked
class TestCertGetDcvParams:
    async def test_posts_payload_to_collection_endpoint(
        self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP
    ) -> None:
        body = {"csr": "-----BEGIN CSR-----", "package": "cert_std_1_0_0", "dcv_method": "dns"}
        payload = {"dcv": [{"type": "TXT", "name": "_acme", "value": "abc"}]}
        route = respx_mock.post("/v5/certificate/dcv_params").mock(return_value=httpx.Response(200, json=payload))

        handler = await _get_handler(write_server, "gandi_cert_get_dcv_params")
        result = await handler(ctx, data=body)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == body
        assert result == payload

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.post("/v5/certificate/dcv_params").mock(return_value=httpx.Response(400, json={}))

        handler = await _get_handler(write_server, "gandi_cert_get_dcv_params")
        with pytest.raises(ToolError):
            await handler(ctx, data={"csr": "bad"})


@pytest.mark.mocked
class TestCertGetCertDcvParams:
    async def test_posts_payload_to_id_scoped_endpoint(
        self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP
    ) -> None:
        body = {"dcv_method": "dns"}
        payload = {"dcv": [{"type": "TXT"}]}
        route = respx_mock.post("/v5/certificate/issued-certs/cert-1/dcv_params").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(write_server, "gandi_cert_get_cert_dcv_params")
        result = await handler(ctx, cert_id="cert-1", data=body)

        assert route.called
        request = route.calls.last.request
        assert request.method == "POST"
        assert json.loads(request.content) == body
        assert result == payload

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        route = respx_mock.post("/v5/certificate/issued-certs/a%2Fb/dcv_params").mock(
            return_value=httpx.Response(200, json={})
        )

        handler = await _get_handler(write_server, "gandi_cert_get_cert_dcv_params")
        await handler(ctx, cert_id="a/b", data={})

        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb/dcv_params"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.post("/v5/certificate/issued-certs/missing/dcv_params").mock(
            return_value=httpx.Response(404, json={})
        )

        handler = await _get_handler(write_server, "gandi_cert_get_cert_dcv_params")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing", data={})


@pytest.mark.mocked
class TestCertResendDcv:
    async def test_puts_empty_body_to_dcv_endpoint(
        self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP
    ) -> None:
        payload = {"message": "DCV resent"}
        route = respx_mock.put("/v5/certificate/issued-certs/cert-1/dcv").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(write_server, "gandi_cert_resend_dcv")
        result = await handler(ctx, cert_id="cert-1")

        assert route.called
        request = route.calls.last.request
        assert request.method == "PUT"
        assert json.loads(request.content) == {}
        assert result == payload

    async def test_handles_204(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.put("/v5/certificate/issued-certs/cert-1/dcv").mock(return_value=httpx.Response(204))

        handler = await _get_handler(write_server, "gandi_cert_resend_dcv")
        result = await handler(ctx, cert_id="cert-1")

        assert result == {}

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        route = respx_mock.put("/v5/certificate/issued-certs/a%2Fb/dcv").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(write_server, "gandi_cert_resend_dcv")
        await handler(ctx, cert_id="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb/dcv"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.put("/v5/certificate/issued-certs/missing/dcv").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(write_server, "gandi_cert_resend_dcv")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing")


@pytest.mark.mocked
class TestCertUpdateDcvMethod:
    async def test_patches_method_to_dcv_endpoint(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        body = {"dcv_method": "email"}
        payload = {"message": "DCV method updated"}
        route = respx_mock.patch("/v5/certificate/issued-certs/cert-1/dcv").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(write_server, "gandi_cert_update_dcv_method")
        result = await handler(ctx, cert_id="cert-1", data=body)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == body
        assert result == payload

    async def test_maps_400_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.patch("/v5/certificate/issued-certs/cert-1/dcv").mock(return_value=httpx.Response(400, json={}))

        handler = await _get_handler(write_server, "gandi_cert_update_dcv_method")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="cert-1", data={"dcv_method": "bogus"})


@pytest.mark.mocked
class TestCertUpdate:
    async def test_patches_metadata_to_id_endpoint(
        self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP
    ) -> None:
        body = {"package": "cert_pro_1_0_0"}
        payload = {"id": "cert-1", "package": "cert_pro_1_0_0"}
        route = respx_mock.patch("/v5/certificate/issued-certs/cert-1").mock(
            return_value=httpx.Response(200, json=payload)
        )

        handler = await _get_handler(write_server, "gandi_cert_update")
        result = await handler(ctx, cert_id="cert-1", data=body)

        assert route.called
        request = route.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == body
        assert result == payload

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        route = respx_mock.patch("/v5/certificate/issued-certs/a%2Fb").mock(return_value=httpx.Response(200, json={}))

        handler = await _get_handler(write_server, "gandi_cert_update")
        await handler(ctx, cert_id="a/b", data={})

        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb"

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, write_server: FastMCP) -> None:
        respx_mock.patch("/v5/certificate/issued-certs/missing").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(write_server, "gandi_cert_update")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing", data={})


@pytest.mark.mocked
class TestCertGetCrt:
    PEM = "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----\n"

    async def test_returns_raw_pem_body(self, ctx: AsyncMock, respx_mock: Any, read_server: FastMCP) -> None:
        route = respx_mock.get("/v5/certificate/issued-certs/cert-1/crt").mock(
            return_value=httpx.Response(200, text=self.PEM, headers={"content-type": "text/plain"})
        )

        handler = await _get_handler(read_server, "gandi_cert_get_crt")
        result = await handler(ctx, cert_id="cert-1")

        assert route.called
        assert route.calls.last.request.method == "GET"
        assert result == self.PEM
        assert isinstance(result, str)

    async def test_sends_text_plain_accept_header(self, ctx: AsyncMock, respx_mock: Any, read_server: FastMCP) -> None:
        route = respx_mock.get("/v5/certificate/issued-certs/cert-1/crt").mock(
            return_value=httpx.Response(200, text=self.PEM)
        )

        handler = await _get_handler(read_server, "gandi_cert_get_crt")
        await handler(ctx, cert_id="cert-1")

        assert route.calls.last.request.headers["accept"] == "text/plain"

    async def test_url_encodes_cert_id(self, ctx: AsyncMock, respx_mock: Any, read_server: FastMCP) -> None:
        route = respx_mock.get("/v5/certificate/issued-certs/a%2Fb/crt").mock(
            return_value=httpx.Response(200, text=self.PEM)
        )

        handler = await _get_handler(read_server, "gandi_cert_get_crt")
        await handler(ctx, cert_id="a/b")

        assert route.calls.last.request.url.raw_path == b"/v5/certificate/issued-certs/a%2Fb/crt"

    async def test_empty_body_raises_tool_error(self, ctx: AsyncMock, respx_mock: Any, read_server: FastMCP) -> None:
        respx_mock.get("/v5/certificate/issued-certs/cert-1/crt").mock(return_value=httpx.Response(200, text=""))

        handler = await _get_handler(read_server, "gandi_cert_get_crt")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="cert-1")

    async def test_maps_404_to_tool_error(self, ctx: AsyncMock, respx_mock: Any, read_server: FastMCP) -> None:
        respx_mock.get("/v5/certificate/issued-certs/missing/crt").mock(return_value=httpx.Response(404, json={}))

        handler = await _get_handler(read_server, "gandi_cert_get_crt")
        with pytest.raises(ToolError):
            await handler(ctx, cert_id="missing")
