"""Shared helpers for tool modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gandi_mcp.errors import GandiPurchaseBlockedError, GandiReadOnlyError

if TYPE_CHECKING:
    from fastmcp import Context

    from gandi_mcp.clients.gandi import GandiClient
    from gandi_mcp.server import ServerContext

# First name segment (after the ``gandi_`` prefix) → display label for the area.
# Acronyms and CamelCase product names that ``str.capitalize`` would mangle.
_AREA_LABELS = {
    "billing": "Billing",
    "cert": "Cert",
    "comment": "Comment",
    "domain": "Domain",
    "email": "Email",
    "linkedzone": "LinkedZone",
    "livedns": "LiveDNS",
    "mailbox": "Mailbox",
    "org": "Org",
    "simplehosting": "SimpleHosting",
    "template": "Template",
}

# Verb/entity words whose canonical casing differs from ``str.capitalize``.
_WORD_LABELS = {
    "dns": "DNS",
    "dnssec": "DNSSEC",
    "dcv": "DCV",
    "crt": "CRT",
    "foa": "FOA",
    "tld": "TLD",
    "tlds": "TLDs",
    "tsig": "TSIG",
    "rrtypes": "RRTypes",
    "livedns": "LiveDNS",
    "vhost": "VHost",
    "transferin": "TransferIn",
    "authinfo": "AuthInfo",
    "autorenew": "AutoRenew",
}


def title_for_tool(name: str) -> str:
    """Derive a human-readable display title from a snake_case tool name.

    Strips the ``gandi_`` prefix, maps the leading segment to an area label,
    and Title-Cases the remaining verb/entity words (with acronym overrides).
    For example ``gandi_domain_list_domains`` becomes ``"Domain: List Domains"``.

    Args:
        name: The tool's protocol name (e.g. ``gandi_cert_get_crt``).

    Returns:
        A display title of the form ``"Area: Verb Entity"``.
    """
    body = name.removeprefix("gandi_")
    area, _, rest = body.partition("_")
    area_label = _AREA_LABELS.get(area, area.capitalize())
    if not rest:
        return area_label
    words = " ".join(_WORD_LABELS.get(word, word.capitalize()) for word in rest.split("_"))
    return f"{area_label}: {words}"


def get_server_context(ctx: Context) -> ServerContext:
    """Return the typed lifespan context for a tool call."""
    return ctx.lifespan_context  # ty: ignore[invalid-return-type]


def get_client(ctx: Context) -> GandiClient:
    """Return the live Gandi client, raising if the lifespan failed to build one.

    The lifespan disables all ``"gandi"``-tagged tools when client construction
    or validation fails, so a handler that reaches this helper without a client
    is either a bug in the lifespan or a stale server instance — either way,
    we want a loud error, not a ``None`` attribute access later.
    """
    context = get_server_context(ctx)
    if context.client is None:
        raise RuntimeError(
            "Gandi client is not initialized — this tool should have been disabled by the server lifespan"
        )
    return context.client


def assert_readwrite(ctx: Context, action: str) -> None:
    """Defense-in-depth: block write tools at runtime in readonly mode.

    Complements the ``mcp.disable(tags={"write"})`` in server setup so that a
    misconfigured or stale tool list can't slip a write through.
    """
    context = get_server_context(ctx)
    if not context.config.is_readwrite:
        raise GandiReadOnlyError(f"Cannot {action} in read-only mode (GANDI_MODE=readonly)")


def assert_purchases_allowed(ctx: Context, action: str) -> None:
    """Defense-in-depth: block purchase tools at runtime when purchases are off.

    Purchase tools are also write tools — this check runs *after* the readwrite
    check in callers, so an operator needs BOTH ``GANDI_MODE=readwrite`` AND
    ``GANDI_ALLOW_PURCHASES=true`` to spend any money.
    """
    context = get_server_context(ctx)
    if not context.config.purchases_enabled:
        raise GandiPurchaseBlockedError(f"Cannot {action} — purchases are disabled (set GANDI_ALLOW_PURCHASES=true)")
