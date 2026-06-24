"""SSL certificate tools (/v5/certificate)."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP

from gandi_mcp.errors import handle_client_error
from gandi_mcp.tools._common import (
    assert_purchases_allowed,
    assert_readwrite,
    get_client,
)


def register_certificate_read_tools(mcp: FastMCP) -> None:
    """Register read-only certificate tools on the server."""

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_list(
        ctx: Context,
        status: str | None = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """List issued SSL certificates.

        Args:
            status: Filter by status ("valid", "expired", "revoked",
                "pending", "replaced").
            per_page: Page size.
            page: Page number.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).cert_list(status=status, per_page=per_page, page=page)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_get(ctx: Context, cert_id: str) -> dict[str, Any]:
        """Retrieve details for a specific certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).cert_get(cert_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_list_tags(ctx: Context, cert_id: str) -> list[str]:
        """List the operator-defined tags on a certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).cert_list_tags(cert_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_list_packages(ctx: Context) -> list[dict[str, Any]]:
        """List available certificate packages (product offerings).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).cert_list_packages()
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_get_package(ctx: Context, name: str) -> dict[str, Any]:
        """Get a single certificate package by name.

        Args:
            name: Package identifier (e.g. "cert_std_1_0_0").

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            return await get_client(ctx).cert_get_package(name)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(tags={"gandi", "certificate"})
    async def gandi_cert_get_crt(ctx: Context, cert_id: str) -> str:
        """Fetch the raw issued certificate (PEM document) for a certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            The PEM-encoded certificate as a raw text string (not JSON).
        """
        try:
            return await get_client(ctx).cert_get_crt(cert_id)
        except Exception as e:
            handle_client_error(e)


def register_certificate_write_tools(mcp: FastMCP) -> None:
    """Register non-purchasing write certificate tools on the server."""

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_cert_revoke(ctx: Context, cert_id: str) -> dict[str, Any]:
        """Revoke an issued certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "revoke certificate")
            return await get_client(ctx).cert_revoke(cert_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_add_tag(ctx: Context, cert_id: str, name: str) -> dict[str, Any]:
        """Add a single operator-defined tag to a certificate.

        Args:
            cert_id: Certificate UUID.
            name: Tag to add.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "add certificate tag")
            return await get_client(ctx).cert_add_tag(cert_id, name)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_cert_replace_tags(ctx: Context, cert_id: str, tags: list[str]) -> dict[str, Any]:
        """Replace the full set of tags on a certificate.

        Args:
            cert_id: Certificate UUID.
            tags: New full tag list (replaces all existing tags).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "replace certificate tags")
            return await get_client(ctx).cert_replace_tags(cert_id, tags)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_update_tags(ctx: Context, cert_id: str, tags: list[str]) -> dict[str, Any]:
        """Add tags to a certificate without removing existing ones.

        Args:
            cert_id: Certificate UUID.
            tags: Tags to add.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update certificate tags")
            return await get_client(ctx).cert_update_tags(cert_id, tags)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": True},
    )
    async def gandi_cert_delete_tags(ctx: Context, cert_id: str) -> dict[str, Any]:
        """Remove all operator-defined tags from a certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "delete certificate tags")
            return await get_client(ctx).cert_delete_tags(cert_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_get_dcv_params(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Compute domain-control-validation parameters for a candidate certificate.

        POST-based parameter computation: it submits a CSR / package / DCV
        method and returns the DCV records to publish. It does not order a
        certificate or spend money, but is a POST and is therefore gated as a
        write.

        Args:
            data: DCV-params request payload per the Gandi certificate schema
                (typically ``csr``, ``package``, ``dcv_method``).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "compute certificate DCV params")
            return await get_client(ctx).cert_get_dcv_params(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_get_cert_dcv_params(ctx: Context, cert_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Compute domain-control-validation parameters for an issued certificate.

        POST-based parameter computation (see ``gandi_cert_get_dcv_params``);
        gated as a write because it is a POST.

        Args:
            cert_id: Certificate UUID.
            data: DCV-params request payload per the Gandi certificate schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "compute certificate DCV params")
            return await get_client(ctx).cert_get_cert_dcv_params(cert_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_resend_dcv(ctx: Context, cert_id: str) -> dict[str, Any]:
        """Resend the domain-control-validation request for a pending certificate.

        Args:
            cert_id: Certificate UUID.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "resend certificate DCV")
            return await get_client(ctx).cert_resend_dcv(cert_id)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_update_dcv_method(ctx: Context, cert_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Change the domain-control-validation method for a pending certificate.

        Args:
            cert_id: Certificate UUID.
            data: DCV-method payload (typically ``dcv_method``: "dns", "email",
                "file", or "http").

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update certificate DCV method")
            return await get_client(ctx).cert_update_dcv_method(cert_id, data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write"},
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )
    async def gandi_cert_update(ctx: Context, cert_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an issued certificate's metadata.

        Args:
            cert_id: Certificate UUID.
            data: Partial update payload per the Gandi certificate schema.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "update certificate")
            return await get_client(ctx).cert_update(cert_id, data)
        except Exception as e:
            handle_client_error(e)


def register_certificate_purchase_tools(mcp: FastMCP) -> None:
    """Register money-spending certificate tools on the server.

    DOUBLE-GATED: requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.
    """

    @mcp.tool(
        tags={"gandi", "certificate", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_cert_issue(ctx: Context, data: dict[str, Any]) -> dict[str, Any]:
        """Issue a new SSL certificate (SPENDS MONEY).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            data: Full issuance payload per the Gandi certificate schema —
                must include ``cn``, ``package``, ``duration``, a CSR, and a
                DCV method.

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "issue certificate")
            assert_purchases_allowed(ctx, "issue certificate")
            return await get_client(ctx).cert_issue(data)
        except Exception as e:
            handle_client_error(e)

    @mcp.tool(
        tags={"gandi", "certificate", "write", "purchase"},
        annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    )
    async def gandi_cert_renew(ctx: Context, cert_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Renew an existing certificate (SPENDS MONEY).

        Requires GANDI_MODE=readwrite AND GANDI_ALLOW_PURCHASES=true.

        Args:
            cert_id: Certificate UUID.
            data: Renewal payload (new CSR, duration, DCV method).

        Returns:
            Gandi API response payload (see `https://api.gandi.net/docs` for the schema).
        """
        try:
            assert_readwrite(ctx, "renew certificate")
            assert_purchases_allowed(ctx, "renew certificate")
            return await get_client(ctx).cert_renew(cert_id, data)
        except Exception as e:
            handle_client_error(e)


def register_certificate_tools(mcp: FastMCP) -> None:
    """Register every certificate tool (read + write + purchase).

    Read/write/purchase visibility is gated separately at the server level via
    ``mcp.disable(tags={...})``; this function unconditionally registers all
    three tiers. Tests that want only one tier should call the granular
    ``register_certificate_<tier>_tools`` helpers directly.
    """
    register_certificate_read_tools(mcp)
    register_certificate_write_tools(mcp)
    register_certificate_purchase_tools(mcp)
