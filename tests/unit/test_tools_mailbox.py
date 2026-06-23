"""Handler-level tests for the mailbox tool surface (``gandi_mailbox_*``).

The schema-drift guard (``test_tool_schema_matrix``) and the static safety-gate
walker pin the *declarations*; this module exercises the handler *bodies* — the
``try: ... except: handle_client_error(e)`` wrappers around each
``get_client(ctx).<method>`` call. Three behaviours per tier:

* happy path — the handler forwards to the client and returns the payload;
* write gate — in readonly mode the ``assert_readwrite`` guard blocks the write
  (surfaced as a ``ToolError`` because the handler wraps it);
* error mapping — a Gandi API error becomes a ``ToolError``.

Handlers are closures registered on a ``FastMCP`` instance, so they're reached
via ``(await server.get_tool(name)).fn`` and called with a fake context that
carries the real ``GandiClient`` and config (mirroring ``build_fake_ctx``).
HTTP is mocked with respx; no network, no real lifespan.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
import respx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from gandi_mcp.clients.gandi import GandiClient
from gandi_mcp.config import GandiConfig, GandiMode
from gandi_mcp.tools.mailbox import register_mailbox_tools
from tests.conftest import build_fake_ctx

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

BASE_URL = "https://api.gandi.net"


def _config(mode: GandiMode = GandiMode.READONLY, *, purchases: bool = False) -> GandiConfig:
    return GandiConfig(
        _env_file=None,
        gandi_token="test-token",
        gandi_mode=mode,
        gandi_allow_purchases=purchases,
    )


@pytest.fixture
def server() -> FastMCP:
    mcp = FastMCP(name="mailbox-test")
    register_mailbox_tools(mcp)
    return mcp


async def _handler(server: FastMCP, name: str) -> Callable[..., Awaitable[Any]]:
    tool = await server.get_tool(name)
    return tool.fn


def _ctx(client: GandiClient, config: GandiConfig) -> Any:
    return build_fake_ctx(config, client=client)


@pytest.fixture
async def client() -> GandiClient:
    c = GandiClient(base_url=BASE_URL, token="test-token", timeout=5, max_retries=1)
    yield c
    await c.close()


class TestReadTools:
    """Each read handler forwards to its client method and returns the payload."""

    async def test_list_domains(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_list_domains")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/domains").mock(
                return_value=httpx.Response(200, json=[{"fqdn": "example.com"}]),
            )
            assert await fn(ctx) == [{"fqdn": "example.com"}]

    async def test_get_domain(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_get_domain")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/domains/example.com").mock(
                return_value=httpx.Response(200, json={"fqdn": "example.com"}),
            )
            assert await fn(ctx, "example.com") == {"fqdn": "example.com"}

    async def test_list_mailboxes(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_list_mailboxes")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/mailboxes").mock(
                return_value=httpx.Response(200, json=[{"address": "a@example.com"}]),
            )
            assert await fn(ctx) == [{"address": "a@example.com"}]

    async def test_get_mailbox(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_get_mailbox")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/mailboxes/a@example.com").mock(
                return_value=httpx.Response(200, json={"address": "a@example.com"}),
            )
            assert await fn(ctx, "a@example.com") == {"address": "a@example.com"}

    async def test_list_forwards(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_list_forwards")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/forwards").mock(
                return_value=httpx.Response(200, json=[{"source": "s@example.com"}]),
            )
            assert await fn(ctx) == [{"source": "s@example.com"}]

    async def test_list_slots(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_list_slots")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/slots").mock(
                return_value=httpx.Response(200, json=[{"id": "slot-1"}]),
            )
            assert await fn(ctx) == [{"id": "slot-1"}]

    async def test_get_slot(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_get_slot")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/slots/slot-1").mock(
                return_value=httpx.Response(200, json={"id": "slot-1"}),
            )
            assert await fn(ctx, "slot-1") == {"id": "slot-1"}

    async def test_get_quotas(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_get_quotas")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/quotas").mock(
                return_value=httpx.Response(200, json={"used": 1}),
            )
            assert await fn(ctx) == {"used": 1}

    async def test_list_products(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_list_products")
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get("/v5/mailbox/products").mock(
                return_value=httpx.Response(200, json=[{"name": "standard"}]),
            )
            assert await fn(ctx) == [{"name": "standard"}]

    @pytest.mark.parametrize(
        ("name", "path", "args"),
        [
            ("gandi_mailbox_list_domains", "/v5/mailbox/domains", ()),
            ("gandi_mailbox_get_domain", "/v5/mailbox/domains/example.com", ("example.com",)),
            ("gandi_mailbox_list_mailboxes", "/v5/mailbox/mailboxes", ()),
            ("gandi_mailbox_get_mailbox", "/v5/mailbox/mailboxes/a@example.com", ("a@example.com",)),
            ("gandi_mailbox_list_forwards", "/v5/mailbox/forwards", ()),
            ("gandi_mailbox_list_slots", "/v5/mailbox/slots", ()),
            ("gandi_mailbox_get_slot", "/v5/mailbox/slots/slot-1", ("slot-1",)),
            ("gandi_mailbox_get_quotas", "/v5/mailbox/quotas", ()),
            ("gandi_mailbox_list_products", "/v5/mailbox/products", ()),
        ],
    )
    async def test_read_tool_maps_api_error(
        self, server: FastMCP, client: GandiClient, name: str, path: str, args: tuple[Any, ...]
    ) -> None:
        """A Gandi API error in any read handler surfaces as a ``ToolError``."""
        fn = await _handler(server, name)
        ctx = _ctx(client, _config())
        with respx.mock(base_url=BASE_URL) as mock:
            mock.get(path).mock(return_value=httpx.Response(404, json={"message": "not found"}))
            with pytest.raises(ToolError, match="not found"):
                await fn(ctx, *args)


class TestWriteTools:
    """Non-purchasing writes: happy path in readwrite, blocked in readonly."""

    async def test_validate_domain(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_validate_domain")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/v5/mailbox/domains/example.com/validate").mock(
                return_value=httpx.Response(200, json={"status": "ok"}),
            )
            assert await fn(ctx, "example.com", {"k": "v"}) == {"status": "ok"}

    async def test_update_mailbox(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_update_mailbox")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.patch("/v5/mailbox/mailboxes/a@example.com").mock(
                return_value=httpx.Response(200, json={"address": "a@example.com"}),
            )
            assert await fn(ctx, "a@example.com", {"login": "a"}) == {"address": "a@example.com"}

    async def test_delete_mailbox(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_delete_mailbox")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete("/v5/mailbox/mailboxes/a@example.com").mock(
                return_value=httpx.Response(202, json={"status": "deleting"}),
            )
            assert await fn(ctx, "a@example.com") == {"status": "deleting"}

    async def test_create_forward(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_create_forward")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/v5/mailbox/forwards").mock(
                return_value=httpx.Response(201, json={"source": "s@example.com"}),
            )
            assert await fn(ctx, {"source": "s@example.com"}) == {"source": "s@example.com"}

    async def test_update_forward(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_update_forward")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.put("/v5/mailbox/forwards/s@example.com").mock(
                return_value=httpx.Response(200, json={"source": "s@example.com"}),
            )
            assert await fn(ctx, "s@example.com", {"destinations": ["d@x.com"]}) == {"source": "s@example.com"}

    async def test_delete_forward(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_delete_forward")
        ctx = _ctx(client, _config(GandiMode.READWRITE))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.delete("/v5/mailbox/forwards/s@example.com").mock(
                return_value=httpx.Response(204),
            )
            assert await fn(ctx, "s@example.com") == {}

    @pytest.mark.parametrize(
        ("name", "args"),
        [
            ("gandi_mailbox_validate_domain", ("example.com", {"k": "v"})),
            ("gandi_mailbox_update_mailbox", ("a@example.com", {"login": "a"})),
            ("gandi_mailbox_delete_mailbox", ("a@example.com",)),
            ("gandi_mailbox_create_forward", ({"source": "s@example.com"},)),
            ("gandi_mailbox_update_forward", ("s@example.com", {"destinations": []})),
            ("gandi_mailbox_delete_forward", ("s@example.com",)),
        ],
    )
    async def test_write_gate_blocks_in_readonly(
        self, server: FastMCP, client: GandiClient, name: str, args: tuple[Any, ...]
    ) -> None:
        """In readonly mode every write handler is blocked before any HTTP call."""
        fn = await _handler(server, name)
        ctx = _ctx(client, _config(GandiMode.READONLY))
        with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
            mock.route().mock(side_effect=AssertionError("no HTTP call expected when gated"))
            with pytest.raises(ToolError, match="read-only mode"):
                await fn(ctx, *args)


class TestPurchaseTools:
    """Money-spending tools: need readwrite + purchases; both gates enforced."""

    async def test_create_mailbox(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_create_mailbox")
        ctx = _ctx(client, _config(GandiMode.READWRITE, purchases=True))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/v5/mailbox/mailboxes").mock(
                return_value=httpx.Response(201, json={"address": "a@example.com"}),
            )
            assert await fn(ctx, {"address": "a@example.com"}) == {"address": "a@example.com"}

    async def test_renew_mailbox(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_renew_mailbox")
        ctx = _ctx(client, _config(GandiMode.READWRITE, purchases=True))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/v5/mailbox/mailboxes/a@example.com/renew").mock(
                return_value=httpx.Response(200, json={"status": "renewed"}),
            )
            assert await fn(ctx, "a@example.com", {"duration": 1}) == {"status": "renewed"}

    async def test_buy_product(self, server: FastMCP, client: GandiClient) -> None:
        fn = await _handler(server, "gandi_mailbox_buy_product")
        ctx = _ctx(client, _config(GandiMode.READWRITE, purchases=True))
        with respx.mock(base_url=BASE_URL) as mock:
            mock.post("/v5/mailbox/products").mock(
                return_value=httpx.Response(201, json={"id": "slot-1"}),
            )
            assert await fn(ctx, {"product": "standard"}) == {"id": "slot-1"}

    @pytest.mark.parametrize(
        ("name", "args"),
        [
            ("gandi_mailbox_create_mailbox", ({"address": "a@example.com"},)),
            ("gandi_mailbox_renew_mailbox", ("a@example.com", {"duration": 1})),
            ("gandi_mailbox_buy_product", ({"product": "standard"},)),
        ],
    )
    async def test_write_gate_blocks_purchase_in_readonly(
        self, server: FastMCP, client: GandiClient, name: str, args: tuple[Any, ...]
    ) -> None:
        """Readonly mode hits the readwrite gate first (the narrower error)."""
        fn = await _handler(server, name)
        ctx = _ctx(client, _config(GandiMode.READONLY))
        with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
            mock.route().mock(side_effect=AssertionError("no HTTP call expected when gated"))
            with pytest.raises(ToolError, match="read-only mode"):
                await fn(ctx, *args)

    @pytest.mark.parametrize(
        ("name", "args"),
        [
            ("gandi_mailbox_create_mailbox", ({"address": "a@example.com"},)),
            ("gandi_mailbox_renew_mailbox", ("a@example.com", {"duration": 1})),
            ("gandi_mailbox_buy_product", ({"product": "standard"},)),
        ],
    )
    async def test_purchase_gate_blocks_when_purchases_off(
        self, server: FastMCP, client: GandiClient, name: str, args: tuple[Any, ...]
    ) -> None:
        """Readwrite alone is not enough — the purchase gate still blocks."""
        fn = await _handler(server, name)
        ctx = _ctx(client, _config(GandiMode.READWRITE, purchases=False))
        with respx.mock(base_url=BASE_URL, assert_all_called=False) as mock:
            mock.route().mock(side_effect=AssertionError("no HTTP call expected when gated"))
            with pytest.raises(ToolError, match="purchases are disabled"):
                await fn(ctx, *args)
