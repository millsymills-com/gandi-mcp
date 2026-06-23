"""Schema-drift guard for ``docs/tool-schema-matrix.md``.

The matrix is a generated, checked-in catalogue of every MCP tool this server
exposes: its safety tier, MCP annotation hints, the ``GandiClient`` method it
wraps, and the Gandi v5 endpoint behind that method. It is the human-readable
contract for the tool surface.

Generation is fully static — tags and annotations are read from the
``@mcp.tool(...)`` decorator literals (mirroring ``test_safety_gates``), the
client method from each handler's ``get_client(ctx).<method>`` call, and the
HTTP verb/path from the ``self.<verb>(<path>)`` call inside that client method.
No network, no event loop.

Two invariants are pinned:

1. :func:`test_matrix_doc_in_sync` — the committed markdown equals a fresh
   render. A new, removed, or retagged tool fails the test until the doc is
   regenerated, so a stale row can't survive review.
2. :func:`test_matrix_matches_registered_surface` — the documented tool names
   equal the names the live FastMCP server registers under a full-access
   config. This catches a tool that is declared but never wired into
   ``register_all_tools`` (or vice versa).

Regenerate after changing the tool surface::

    uv run python tests/unit/test_tool_schema_matrix.py
"""

from __future__ import annotations

import ast
import pathlib
import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from gandi_mcp.server import create_server

if TYPE_CHECKING:
    from gandi_mcp.config import GandiConfig

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "src" / "gandi_mcp" / "tools"
CLIENT_FILE = REPO_ROOT / "src" / "gandi_mcp" / "clients" / "gandi.py"
MATRIX_DOC = REPO_ROOT / "docs" / "tool-schema-matrix.md"

SKIP_FILES = frozenset({"__init__.py", "_common.py"})
STRUCTURAL_TAGS = frozenset({"gandi", "write", "purchase"})
HTTP_VERBS = frozenset({"get", "post", "put", "patch", "delete"})
TIER_ORDER = {"read": 0, "write": 1, "purchase": 2}

# Client methods whose path is assembled at runtime rather than a single string
# literal, so the AST renderer can't recover it. Keep this map tiny and obvious;
# a method that grows a dynamic path must be added here or generation fails loudly.
DYNAMIC_ENDPOINTS = {
    "livedns_list_records": ("GET", "/v5/livedns/domains/{fqdn}/records[/{name}[/{rrset_type}]]"),
}


@dataclass(frozen=True)
class ToolRow:
    """One row of the coverage matrix — a tool and the schema it resolves to."""

    area: str
    tier: str
    name: str
    destructive: bool
    open_world: bool
    client_method: str
    verb: str
    endpoint: str


# ── AST extraction ──────────────────────────────────────────────────────────


def _tool_decorator(func: ast.AsyncFunctionDef) -> ast.Call | None:
    """The ``@mcp.tool(...)`` decorator call on ``func``, or ``None``.

    Matched as ``mcp.tool`` specifically, not any ``<x>.tool(...)``: a future
    helper carrying a differently-scoped ``.tool``-named decorator would
    otherwise inject a phantom row.
    """
    for dec in func.decorator_list:
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr == "tool"
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "mcp"
        ):
            return dec
    return None


def _decorator_kw(decorator: ast.Call, name: str) -> ast.expr | None:
    for kw in decorator.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _tag_set(decorator: ast.Call) -> set[str]:
    """String tags from ``tags={...}``; only a ``Set`` of string constants counts."""
    value = _decorator_kw(decorator, "tags")
    if not isinstance(value, ast.Set):
        return set()
    return {e.value for e in value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}


def _annotation_flag(decorator: ast.Call, key: str) -> bool:
    """Boolean ``annotations={...}`` hint; absent reads as ``False``.

    A non-literal value (``destructiveHint=SOME_CONST``) is rejected rather
    than coerced: silently reading it as ``False`` could let the matrix assert
    a destructive tool is non-destructive with no test failure.
    """
    value = _decorator_kw(decorator, "annotations")
    if not isinstance(value, ast.Dict):
        return False
    for k, v in zip(value.keys, value.values, strict=True):
        if isinstance(k, ast.Constant) and k.value == key:
            if not isinstance(v, ast.Constant) or not isinstance(v.value, bool):
                raise ValueError(f"annotation {key!r} must be a literal bool, got {ast.dump(v)}")
            return v.value
    return False


def _client_method(func: ast.AsyncFunctionDef) -> str:
    """The ``<method>`` in the handler's ``get_client(ctx).<method>(...)`` call.

    ``ast.walk`` order is not source order, so a handler making two
    ``get_client`` calls would have one picked arbitrarily and the other
    silently dropped — the row would document a real but possibly wrong
    endpoint while every oracle stayed green. Today the surface is strictly
    one client call per handler; we raise on any other count to pin that.
    """
    methods = [
        node.func.attr
        for node in ast.walk(func)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "get_client"
        )
    ]
    if len(methods) != 1:
        raise ValueError(f"{func.name}: expected exactly one get_client(ctx).<method> call, found {len(methods)}")
    return methods[0]


def _format_field_name(node: ast.expr) -> str:
    """Recover the placeholder name from an f-string ``{...}`` expression.

    ``{_seg(fqdn)}`` renders as ``{fqdn}`` — the percent-encoding helper is
    noise in a URL template, so we unwrap to its first argument's name.
    """
    if isinstance(node, ast.Call) and node.args:
        return _format_field_name(node.args[0])
    name = next((n.id for n in ast.walk(node) if isinstance(n, ast.Name)), None)
    return name or "?"


def _render_path(node: ast.expr) -> str | None:
    """Render a literal or f-string path into a ``{placeholder}`` URL template."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for piece in node.values:
            if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                parts.append(piece.value)
            elif isinstance(piece, ast.FormattedValue):
                parts.append("{" + _format_field_name(piece.value) + "}")
        return "".join(parts)
    return None


def _client_endpoints() -> dict[str, tuple[str, str]]:
    """Map every ``GandiClient`` method to its ``(VERB, path-template)``."""
    tree = ast.parse(CLIENT_FILE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    endpoints: dict[str, tuple[str, str]] = {}
    for method in cls.body:
        if not isinstance(method, ast.AsyncFunctionDef):
            continue
        if method.name in DYNAMIC_ENDPOINTS:
            endpoints[method.name] = DYNAMIC_ENDPOINTS[method.name]
            continue
        for node in ast.walk(method):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr in HTTP_VERBS
                and node.args
            ):
                path = _render_path(node.args[0])
                if path is not None:
                    endpoints[method.name] = (node.func.attr.upper(), path)
                break
    return endpoints


def build_rows() -> list[ToolRow]:
    """Extract every tool's schema row, sorted by (area, tier, name)."""
    endpoints = _client_endpoints()
    rows: list[ToolRow] = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        if path.name in SKIP_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for func in ast.walk(tree):
            if not isinstance(func, ast.AsyncFunctionDef):
                continue
            decorator = _tool_decorator(func)
            if decorator is None:
                continue
            tags = _tag_set(decorator)
            area = sorted(tags - STRUCTURAL_TAGS)
            tier = "purchase" if "purchase" in tags else "write" if "write" in tags else "read"
            method = _client_method(func)
            verb, endpoint = endpoints.get(method, ("?", "?"))
            rows.append(
                ToolRow(
                    area="/".join(area) if area else "?",
                    tier=tier,
                    name=func.name,
                    destructive=_annotation_flag(decorator, "destructiveHint"),
                    open_world=_annotation_flag(decorator, "openWorldHint"),
                    client_method=method,
                    verb=verb,
                    endpoint=endpoint,
                )
            )
    rows.sort(key=lambda r: (r.area, TIER_ORDER[r.tier], r.name))
    return rows


# ── Markdown rendering ──────────────────────────────────────────────────────


def render_markdown(rows: list[ToolRow]) -> str:
    """Render rows into the committed ``docs/tool-schema-matrix.md`` body."""
    by_tier = {tier: sum(1 for r in rows if r.tier == tier) for tier in TIER_ORDER}
    summary = ", ".join(f"{by_tier[t]} {t}" for t in TIER_ORDER)
    lines = [
        "# Tool / schema coverage matrix",
        "",
        "<!-- GENERATED FILE — do not edit by hand.",
        "     Regenerate: uv run python tests/unit/test_tool_schema_matrix.py",
        "     Guarded by: tests/unit/test_tool_schema_matrix.py -->",
        "",
        "Every MCP tool this server exposes, mapped to its safety tier, MCP annotation",
        "hints, the `GandiClient` method it calls, and the Gandi v5 endpoint behind that",
        "method. `tests/unit/test_tool_schema_matrix.py` fails if this table drifts from",
        "the registered tool surface.",
        "",
        "Tiers follow the three-tier safety model: **read** (always visible), **write**",
        "(needs `GANDI_MODE=readwrite`), **purchase** (also needs `GANDI_ALLOW_PURCHASES=true`).",
        "Destructive and open-world columns reflect the tool's MCP annotation hints.",
        "",
        f"**{len(rows)} tools** — {summary}.",
        "",
        "| Area | Tier | Tool | Destructive | Open-world | Client method | Gandi v5 endpoint |",
        "|------|------|------|:-----------:|:----------:|---------------|-------------------|",
    ]
    lines.extend(
        f"| {r.area} | {r.tier} | `{r.name}` | {_yn(r.destructive)} | {_yn(r.open_world)} "
        f"| `{r.client_method}` | `{r.verb} {r.endpoint}` |"
        for r in rows
    )
    lines.append("")
    return "\n".join(lines)


def _yn(flag: bool) -> str:
    return "yes" if flag else "no"


# ── Tests ───────────────────────────────────────────────────────────────────


def test_every_tool_resolves_to_an_endpoint() -> None:
    """No row may carry a ``?`` — every tool must map to a known client endpoint.

    A ``?`` means a handler calls a client method that no longer exists, or a
    client method grew a dynamic path not registered in ``DYNAMIC_ENDPOINTS``.
    Either is a real defect the human-readable matrix would otherwise hide.
    """
    rows = build_rows()
    assert rows, "no tools discovered — generator is broken"
    unresolved = [r.name for r in rows if "?" in (r.area, r.client_method, r.verb, r.endpoint)]
    assert not unresolved, f"tools with an unresolved schema cell: {unresolved}"


def test_matrix_doc_in_sync() -> None:
    """The committed matrix must equal a fresh render of the live tool surface."""
    expected = render_markdown(build_rows())
    actual = MATRIX_DOC.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/tool-schema-matrix.md is stale — regenerate with:\n"
        "    uv run python tests/unit/test_tool_schema_matrix.py"
    )


def _parse_func(source: str) -> ast.AsyncFunctionDef:
    """Parse one ``async def`` from a source snippet for guard unit tests."""
    func = ast.parse(textwrap.dedent(source)).body[0]
    assert isinstance(func, ast.AsyncFunctionDef)
    return func


def test_client_method_rejects_multiple_get_client_calls() -> None:
    """Two client calls in one handler is wrong-but-valid drift — must raise."""
    func = _parse_func("""
        async def h(ctx):
            await get_client(ctx).read_it(x)
            return await get_client(ctx).write_it(x)
    """)
    with pytest.raises(ValueError, match="exactly one get_client"):
        _client_method(func)


def test_client_method_rejects_zero_get_client_calls() -> None:
    """A handler with no client call can't be mapped to an endpoint — must raise."""
    func = _parse_func("""
        async def h(ctx):
            return {}
    """)
    with pytest.raises(ValueError, match="found 0"):
        _client_method(func)


def test_tool_decorator_ignores_non_mcp_tool() -> None:
    """A ``.tool``-named decorator that isn't ``mcp.tool`` injects no phantom row."""
    func = _parse_func("""
        @helper.tool(tags={"gandi"})
        async def h(ctx):
            return await get_client(ctx).read_it(x)
    """)
    assert _tool_decorator(func) is None


def test_annotation_flag_rejects_non_literal() -> None:
    """A non-literal hint must fail loudly, not silently read as ``False``."""
    decorator = _parse_func("""
        @mcp.tool(annotations={"destructiveHint": SOME_CONST})
        async def h(ctx):
            return await get_client(ctx).write_it(x)
    """).decorator_list[0]
    assert isinstance(decorator, ast.Call)
    with pytest.raises(ValueError, match="must be a literal bool"):
        _annotation_flag(decorator, "destructiveHint")


async def test_matrix_matches_registered_surface(readwrite_with_purchases_config: GandiConfig) -> None:
    """Documented tool names must equal what the full-access server registers.

    Generation reads the decorator declarations; this pins that every declared
    tool is actually wired into ``register_all_tools`` and exposed when both
    safety flags are open — catching a declared-but-unregistered tool that pure
    AST extraction would miss.
    """
    server = create_server(readwrite_with_purchases_config)
    registered = {t.name for t in await server.list_tools()}
    documented = {r.name for r in build_rows()}
    assert documented == registered, (
        f"declared-but-unregistered: {sorted(documented - registered)}; "
        f"registered-but-undocumented: {sorted(registered - documented)}"
    )


if __name__ == "__main__":
    MATRIX_DOC.write_text(render_markdown(build_rows()), encoding="utf-8")
    print(f"wrote {MATRIX_DOC.relative_to(REPO_ROOT)}")  # noqa: T201 — regen CLI feedback
