"""Tests for BaseGandiClient retry semantics."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastmcp.exceptions import ToolError

from gandi_mcp.clients.base import BaseGandiClient
from gandi_mcp.errors import GandiConnectionError, GandiTimeoutError, handle_client_error


class TestRetrySemantics:
    """max_retries is a total-attempt count, not an extra-retry count.

    Previously `ge=0` was allowed, which passed stop_after_attempt(0) to tenacity
    — that stops before the first attempt, breaking every request. Config now
    enforces ge=1 so this footgun can't fire.
    """

    @pytest.mark.asyncio
    async def test_max_retries_one_attempts_exactly_once(self) -> None:
        client = BaseGandiClient(base_url="https://api.gandi.net", token="t", max_retries=1)
        with respx.mock(base_url="https://api.gandi.net") as mock:
            route = mock.get("/v5/organization/user-info").mock(side_effect=httpx.ConnectError("boom"))
            with pytest.raises(GandiConnectionError):
                await client.get("/v5/organization/user-info")
            # With max_retries=1 there is no retry — one attempt, then surface the error.
            assert route.call_count == 1
        await client.close()


class TestConnectTimeoutOnWrites:
    """A connection-phase timeout on a non-idempotent write is safe to retry.

    ``httpx.ConnectTimeout`` subclasses ``TimeoutException`` (not ``ConnectError``)
    yet the connection was never established, so the request never reached the
    server. Retrying cannot double-spend, and the agent must not be told the
    write "may have taken effect" (closes #215).
    """

    @pytest.mark.asyncio
    async def test_post_connect_timeout_is_retried(self) -> None:
        client = BaseGandiClient(base_url="https://api.gandi.net", token="t", max_retries=3)
        with respx.mock(base_url="https://api.gandi.net") as mock:
            route = mock.post("/v5/domain/domains").mock(side_effect=httpx.ConnectTimeout("connect timed out"))
            with pytest.raises(GandiConnectionError) as exc_info:
                await client.post("/v5/domain/domains", json={})
            assert not isinstance(exc_info.value, GandiTimeoutError)
            assert route.call_count == 3
        await client.close()

    def test_connect_timeout_message_omits_partial_write_warning(self) -> None:
        """The surfaced ToolError must not claim the write may have taken effect."""
        error = GandiConnectionError("connect timed out")
        with pytest.raises(ToolError) as exc_info:
            handle_client_error(error)
        assert "may or may not" not in str(exc_info.value)
        assert "check state before retrying" not in str(exc_info.value)
