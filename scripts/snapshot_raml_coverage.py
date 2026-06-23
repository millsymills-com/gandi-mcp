"""Snapshot the live Gandi v5 RAML endpoint set into a committed artifact.

There is no vendored Gandi OpenAPI/RAML spec to diff against, so the
tool-schema matrix can only guard self-consistency. This script fetches the
live API docs (``https://api.gandi.net/docs/``), which are server-rendered
per area, and records the set of ``/v5`` endpoints so the test suite can
report *real* coverage (covered / live-denominator) and flag uncovered live
endpoints when Gandi adds them.

Each documented endpoint renders as an in-page anchor of the form
``#<verb>-v5-<area>-<...>`` (e.g. ``#delete-v5-certificate-issued-certs-id-tags``).
These anchors are the canonical per-endpoint identity — one per method+path —
and are far more reliable than counting ``raml-method-verb`` spans, which the
docs emit twice per endpoint (nav + body).

The snapshot is keyed by the ``/v5/<area>`` path segment so it lines up with
the endpoint templates in ``docs/tool-schema-matrix.md`` (which also start
``/v5/<area>/``).

Refresh workflow (re-run whenever Gandi edits the docs)::

    uv run python scripts/snapshot_raml_coverage.py --date 2026-06-23

The ``--date`` is the pull date recorded in the artifact; pass today's date.
Commit the regenerated ``tests/data/raml_coverage_snapshot.json``. If the
refresh raises any area's endpoint count, the real-coverage test will fail
until tools are added (or the documented coverage floor is intentionally
adjusted), surfacing the new live endpoints.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

import httpx

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAPSHOT = REPO_ROOT / "tests" / "data" / "raml_coverage_snapshot.json"
DOCS_ROOT = "https://api.gandi.net/docs/"

# Anchor for one documented endpoint: #<verb>-v5-<rest>. The area is the token
# immediately after ``v5-``. Param segments render with their RAML name (e.g.
# ``id``) and braces stripped, so the anchor is method+path granular but not a
# 1:1 string match for the matrix's ``{param}`` templates — counts are compared.
_ANCHOR = re.compile(r'href="#((get|post|put|patch|delete)-v5-([a-z0-9_]+)[a-z0-9_-]*)"')

# Area sub-pages linked from the docs index (``href="./<area>/"``).
_AREA_LINK = re.compile(r'href="\./([a-z0-9-]+)/"')


def _fetch(client: httpx.Client, url: str) -> str:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.text


def discover_area_pages(index_html: str) -> list[str]:
    """Distinct area sub-page slugs linked from the docs index."""
    return sorted({m.group(1) for m in _AREA_LINK.finditer(index_html)})


def extract_endpoints(page_html: str) -> dict[str, set[str]]:
    """Map ``/v5`` area segment → set of endpoint anchor ids on the page."""
    by_area: dict[str, set[str]] = {}
    for match in _ANCHOR.finditer(page_html):
        anchor, _verb, area = match.group(1), match.group(2), match.group(3)
        by_area.setdefault(area, set()).add(anchor)
    return by_area


def build_snapshot(date: str) -> dict[str, object]:
    """Fetch the docs and assemble the snapshot payload."""
    areas: dict[str, set[str]] = {}
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        index = _fetch(client, DOCS_ROOT)
        for slug in discover_area_pages(index):
            try:
                page = _fetch(client, f"{DOCS_ROOT}{slug}/")
            except httpx.HTTPError as exc:
                raise SystemExit(
                    f"FATAL: failed to fetch area page {slug!r} ({exc}). Refusing to write an under-counted "
                    f"snapshot — a partial fetch would silently ratchet EXPECTED_LIVE_TOTAL down and mask "
                    f"endpoints. Re-run once the docs are reachable."
                ) from exc
            for area, endpoints in extract_endpoints(page).items():
                areas.setdefault(area, set()).update(endpoints)

    areas_out = {
        area: {"count": len(endpoints), "endpoints": sorted(endpoints)} for area, endpoints in sorted(areas.items())
    }
    total = sum(a["count"] for a in areas_out.values())  # type: ignore[misc]
    return {
        "source": DOCS_ROOT,
        "pull_date": date,
        "total": total,
        "areas": areas_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Pull date to record (YYYY-MM-DD)")
    args = parser.parse_args()

    snapshot = build_snapshot(args.date)
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    areas = snapshot["areas"]
    print(  # noqa: T201 — CLI feedback
        f"wrote {SNAPSHOT.relative_to(REPO_ROOT)}: {snapshot['total']} endpoints across {len(areas)} areas "  # type: ignore[arg-type]
        f"(pull_date={snapshot['pull_date']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
