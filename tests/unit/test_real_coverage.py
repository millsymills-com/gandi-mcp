"""Real Gandi v5 API coverage guard (complements the self-consistency matrix).

``test_tool_schema_matrix`` proves the matrix doc matches the registered tool
surface, but it cannot tell whether that surface covers the *actual* Gandi API —
there is no vendored spec to diff against. This module closes that gap using the
committed live snapshot in ``tests/data/raml_coverage_snapshot.json`` (refreshed
by ``scripts/snapshot_raml_coverage.py``).

Coverage is compared per ``/v5/<area>`` segment, count-based: the snapshot
records the number of distinct documented endpoints per area; ``build_rows``
yields the distinct (verb, endpoint-template) pairs the tools wrap. Exact
endpoint-string matching is impossible because the live docs render path params
with generic RAML names (``{id}``) while the client uses domain names
(``{cert_id}``) — so counts, not identities, are the contract.

Two ratchets are pinned:

* ``MIN_COVERED_ENDPOINTS`` — coverage must never regress below the committed
  floor. Raise it as new tools land (the failure message prints the current
  number to copy in).
* ``EXPECTED_LIVE_TOTAL`` — a snapshot refresh that changes the live endpoint
  count trips this until a human acknowledges the new endpoints (by adding
  tools and/or bumping the constants). This is how *new uncovered live
  endpoints* surface.

Run as a script to print the full coverage report::

    uv run python tests/unit/test_real_coverage.py
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.unit.test_tool_schema_matrix import build_rows  # noqa: E402 — needs REPO_ROOT on path in script mode

SNAPSHOT = REPO_ROOT / "tests" / "data" / "raml_coverage_snapshot.json"

# Ratchets — see module docstring. Bump together with the snapshot/tool surface.
EXPECTED_LIVE_TOTAL = 210
MIN_COVERED_ENDPOINTS = 176


def _load_snapshot() -> dict[str, object]:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def covered_by_area() -> dict[str, set[tuple[str, str]]]:
    """Distinct (verb, endpoint-template) pairs the tools wrap, keyed by /v5 area."""
    by_area: dict[str, set[tuple[str, str]]] = {}
    for row in build_rows():
        parts = row.endpoint.split("/")
        if len(parts) > 2 and parts[1] == "v5":
            by_area.setdefault(parts[2], set()).add((row.verb, row.endpoint))
    return by_area


def _coverage_table() -> list[tuple[str, int, int]]:
    """``(area, covered, live)`` rows sorted by area, union of both key sets."""
    snapshot = _load_snapshot()
    live = {area: info["count"] for area, info in snapshot["areas"].items()}  # type: ignore[union-attr]
    covered = {area: len(pairs) for area, pairs in covered_by_area().items()}
    return [(area, covered.get(area, 0), live.get(area, 0)) for area in sorted(set(live) | set(covered))]


def test_live_total_matches_snapshot() -> None:
    """A docs refresh that moves the live denominator must be acknowledged.

    When Gandi adds endpoints and the snapshot is re-pulled, ``total`` changes
    and this trips — forcing a human to add tools and/or bump the constants,
    which is exactly when new uncovered live endpoints should be reviewed.
    """
    total = _load_snapshot()["total"]
    assert total == EXPECTED_LIVE_TOTAL, (
        f"live endpoint total is {total}, expected {EXPECTED_LIVE_TOTAL}. The snapshot was refreshed "
        f"(Gandi changed the docs). Review the new/removed endpoints, then update EXPECTED_LIVE_TOTAL."
    )


def test_coverage_does_not_regress() -> None:
    """Total covered endpoints must stay at or above the committed floor."""
    covered = sum(c for _, c, _ in _coverage_table())
    assert covered >= MIN_COVERED_ENDPOINTS, (
        f"real coverage regressed: {covered} endpoints covered, floor is {MIN_COVERED_ENDPOINTS}."
    )


def test_no_area_over_covers_live() -> None:
    """No area may wrap more endpoints than the live snapshot lists.

    ``covered > live`` means either a tool's endpoint template points at a path
    that is not in the live docs (a wrong-but-valid drift the self-consistency
    matrix can't catch) or the snapshot is stale and needs a refresh.
    """
    offenders = [(area, c, live) for area, c, live in _coverage_table() if c > live]
    assert not offenders, (
        "tools wrap endpoints absent from the live snapshot (wrong path or stale snapshot): "
        + ", ".join(f"{a}: covered {c} > live {live}" for a, c, live in offenders)
    )


def _render_report() -> str:
    table = _coverage_table()
    covered_total = sum(c for _, c, _ in table)
    live_total = sum(live for _, _, live in table)
    pct = 100 * covered_total / live_total if live_total else 0.0
    lines = [f"Real v5 coverage: {covered_total}/{live_total} = {pct:.1f}%", ""]
    lines += [f"  {area:<14} {c:>3} / {live:<3}" for area, c, live in table]
    return "\n".join(lines)


if __name__ == "__main__":
    print(_render_report())  # noqa: T201 — report CLI
