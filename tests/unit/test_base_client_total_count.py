"""``BaseGandiClient.get`` logs Gandi's ``Total-Count`` for list responses (#216).

List endpoints return only the requested page in the body while reporting the
full collection size in the ``Total-Count`` header. Without surfacing that count
a large account silently truncates to the first page with no signal that more
records exist. ``get`` logs the count to stderr (via the module logger) when the
header is present, and stays silent when it isn't.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx
import pytest
import respx

from gandi_mcp.clients.base import BaseGandiClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def make_client() -> AsyncIterator[BaseGandiClient]:
    c = BaseGandiClient(base_url="https://api.gandi.net", token="t", max_retries=1)
    try:
        yield c
    finally:
        await c.close()


class TestTotalCountLogging:
    @pytest.mark.asyncio
    async def test_logs_total_count_when_header_present(self, caplog: pytest.LogCaptureFixture) -> None:
        """A list response whose total exceeds the page size logs the count and path."""
        async with make_client() as client, respx.mock(base_url="https://api.gandi.net") as mock:
            mock.get("/v5/domain/domains").mock(
                return_value=httpx.Response(200, json=[{"fqdn": "a.com"}], headers={"Total-Count": "732"}),
            )
            with caplog.at_level(logging.INFO, logger="gandi_mcp.clients.base"):
                result = await client.get("/v5/domain/domains", params={"per_page": "100"})
        assert result == [{"fqdn": "a.com"}]
        records = [r for r in caplog.records if "Total-Count" in r.getMessage()]
        assert len(records) == 1
        message = records[0].getMessage()
        assert "732" in message
        assert "/v5/domain/domains" in message

    @pytest.mark.asyncio
    async def test_no_log_when_header_absent(self, caplog: pytest.LogCaptureFixture) -> None:
        """A response without the header (e.g. a single-object GET) logs nothing."""
        async with make_client() as client, respx.mock(base_url="https://api.gandi.net") as mock:
            mock.get("/v5/organization/user-info").mock(return_value=httpx.Response(200, json={"username": "demo"}))
            with caplog.at_level(logging.INFO, logger="gandi_mcp.clients.base"):
                result = await client.get("/v5/organization/user-info")
        assert result == {"username": "demo"}
        assert not [r for r in caplog.records if "Total-Count" in r.getMessage()]
