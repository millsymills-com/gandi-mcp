"""Parser regression tests for scripts/snapshot_raml_coverage.py.

Offline-pure: feeds fixture HTML to the anchor/area regexes so a docs-format
change that breaks parsing is caught in CI instead of silently producing an
empty or under-counted snapshot.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "snapshot_raml_coverage.py"

_spec = importlib.util.spec_from_file_location("snapshot_raml_coverage", SCRIPT)
assert _spec is not None
assert _spec.loader is not None
snapshot = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("snapshot_raml_coverage", snapshot)
_spec.loader.exec_module(snapshot)


# Two tricky cases baked in:
#   1. The same endpoint anchor is emitted twice (nav + body) — must dedup to one.
#   2. An area token is followed by a hyphenated rest (``vhosts-fqdn-tags``) — the
#      area must resolve to the bare token, with the trailing hyphens kept in the
#      anchor id, not bleeding into the area key.
FIXTURE_HTML = """
<html>
  <a href="./domain/">Domain</a>
  <a href="./simplehosting/">Simple Hosting</a>
  <nav>
    <a href="#get-v5-domain-domains">List domains</a>
  </nav>
  <body>
    <a href="#get-v5-domain-domains">List domains</a>
    <a href="#post-v5-domain-domains">Create domain</a>
    <a href="#delete-v5-simplehosting-vhosts-fqdn-tags">Delete vhost tags</a>
  </body>
</html>
"""


def test_discover_area_pages_returns_sorted_distinct_slugs() -> None:
    assert snapshot.discover_area_pages(FIXTURE_HTML) == ["domain", "simplehosting"]


def test_extract_endpoints_dedups_nav_and_body_duplicate_anchors() -> None:
    by_area = snapshot.extract_endpoints(FIXTURE_HTML)
    # The domain list anchor appears in both nav and body but counts once.
    assert by_area["domain"] == {"get-v5-domain-domains", "post-v5-domain-domains"}


def test_extract_endpoints_keys_area_on_bare_token_not_hyphenated_rest() -> None:
    by_area = snapshot.extract_endpoints(FIXTURE_HTML)
    # Area key is the bare token; the hyphenated path rest stays in the anchor id.
    assert set(by_area) == {"domain", "simplehosting"}
    assert by_area["simplehosting"] == {"delete-v5-simplehosting-vhosts-fqdn-tags"}


def test_extract_endpoints_empty_on_unparseable_html() -> None:
    # A docs-format change that drops the ``#<verb>-v5-`` anchors yields nothing,
    # which downstream surfaces as a coverage/total regression rather than a crash.
    assert snapshot.extract_endpoints("<html><a href='#overview'>Docs</a></html>") == {}
