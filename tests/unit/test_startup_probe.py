"""Synthetic scoped-PAT startup tests: no live credentials or network."""

import httpx
import pytest
import respx
from pydantic import ValidationError

from gandi_mcp.config import GandiConfig, GandiMode, GandiStartupProbe
from gandi_mcp.server import create_server


def config(**kwargs):
    return GandiConfig(_env_file=None, gandi_token="synthetic", gandi_max_retries=1, **kwargs)


@pytest.mark.parametrize("value", ["none", "auto", "https://other.invalid", "/v5/livedns/domains", ""])
def test_probe_choice_rejects_bypass_and_urls(value):
    with pytest.raises(ValidationError):
        config(gandi_startup_probe=value)


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [[], [{"fqdn": "example.test"}]])
@pytest.mark.parametrize(("mode", "purchases"), [("readonly", False), ("readonly", True), ("readwrite", False)])
async def test_livedns_success_preserves_gates_and_scope(body, mode, purchases):
    server = create_server(
        config(
            gandi_startup_probe=GandiStartupProbe.LIVEDNS,
            gandi_sharing_id="synthetic-org",
            gandi_mode=mode,
            gandi_allow_purchases=purchases,
        )
    )
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get(
            "https://api.gandi.net/v5/livedns/domains",
            params={"page": "1", "per_page": "1", "sharing_id": "synthetic-org"},
        ).respond(200, json=body)
        async with server._lifespan(server) as ctx:
            assert ctx.client is not None
            tools = await server.list_tools()
            assert tools
            assert all("purchase" not in t.tags for t in tools)
            if mode == "readonly":
                assert all("write" not in t.tags for t in tools)
        assert route.call_count == len(mock.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body"),
    [(401, {}), (403, {}), (404, {}), (429, {}), (500, {}), (302, []), (204, None), (200, {}), (200, ["invalid"])],
)
async def test_livedns_failure_disables_all_tools_without_fallback(status, body):
    server = create_server(
        config(
            gandi_startup_probe=GandiStartupProbe.LIVEDNS, gandi_mode=GandiMode.READWRITE, gandi_allow_purchases=True
        )
    )
    with respx.mock(assert_all_called=True) as mock:
        route = mock.get("https://api.gandi.net/v5/livedns/domains").respond(
            status, json=body, headers={"Location": "https://other.invalid/"}
        )
        async with server._lifespan(server) as ctx:
            assert ctx.client is None
            assert await server.list_tools() == []
        assert route.call_count == len(mock.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [httpx.ConnectError("synthetic"), httpx.ReadTimeout("synthetic")])
async def test_livedns_network_failure_is_not_readiness(error):
    server = create_server(config(gandi_startup_probe=GandiStartupProbe.LIVEDNS))
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.gandi.net/v5/livedns/domains").mock(side_effect=error)
        async with server._lifespan(server) as ctx:
            assert ctx.client is None
            assert await server.list_tools() == []
        assert len(mock.calls) == 1


@pytest.mark.asyncio
async def test_default_probe_stays_user_info_and_never_falls_back():
    server = create_server(config())
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://api.gandi.net/v5/organization/user-info").respond(403, json={})
        async with server._lifespan(server) as ctx:
            assert ctx.client is None
            assert await server.list_tools() == []
        assert len(mock.calls) == 1
