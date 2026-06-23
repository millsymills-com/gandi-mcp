# Implementation Plan: Raise Gandi MCP v5 API Coverage to >=90%

**Status:** Proposed
**Target:** >=90% of live Gandi v5 endpoints covered by registered tools + client methods
**Current:** 71 tools / 70 client methods across 6 areas (domain, livedns, email, certificate, billing, organization) = **34.6% of 208** live `/v5` endpoints.
**Denominator:** locked from Gandi's live RAML docs on 2026-06-23 (no OpenAPI spec exists — see §1). Five areas have **zero** tools: `mailbox`, `linkedzone`, `comment`, `simplehosting`, `template`.

---

## 1. Coverage math

### Denominator source (locked)

**Gandi publishes no OpenAPI/Swagger spec.** The public API reference at `https://api.gandi.net/docs/` is generated from **RAML** and rendered to HTML (`raml-method-verb-*` classes; per-endpoint permalink anchors `#{verb}-v5-{path}`). The denominator below was locked on **2026-06-23** by counting `raml-method-verb` spans per section across the live docs — the authoritative per-endpoint signal — not by prose scraping. Re-pull to refresh.

This pull corrected the first (workflow) estimate of 173, which **missed three entire product areas** and undercounted the rest:

- **`mailbox` (18)** — Gandi's current mailbox product, distinct from the legacy `email` area we already cover.
- **`linkedzone` (12)** — LiveDNS linked/shared zones (`/v5/linkedzone/*`).
- **`comment` (3)** — generic object comments (`/v5/comment/comments/{id}`).

Non-`/v5` or prose-only sections with **zero** RAML methods are excluded from the denominator: `authentication` (OAuth, prose), `gandicloud` (GandiCloud **VPS** — a separate non-`/v5` product), `migration` (prose; the actual migration calls live under `mailbox`/`email`).

| Metric | Value |
|---|---|
| Live RAML `/v5` endpoints (11 areas) | **208** |
| Currently covered (registered tools) | 72 |
| **Current coverage** | **34.6%** |
| 90% threshold | **188 covered** |
| **New tools to implement** | **116** |

> The denominator keeps the 2 previously "documented-impossible" domain endpoints (`PATCH /v5/domain/domains/{domain}/status`, `POST /v5/domain/domains/{domain}/transferout`) **in** the count, because the live RAML *does* render them as `/v5` methods. CLAUDE.md records them as v5 gaps — that note must be reconciled against the live spec (see Risks §5). They are flagged needs-verification, not auto-included in the build.
>
> The repo registers 71 tools / 70 client methods; the 72 vs 71 delta is one tool sharing a client method (a convenience wrapper) and does not affect endpoint counting.

### Per-area coverage (current, locked denominator)

| Area | Covered | Total | % | Missing |
|---|---|---|---|---|
| billing | 3 | 3 | 100% | 0 |
| email | 15 | 20 | 75% | 5 |
| domain | 26 | 57 | 45.6% | 31 |
| livedns | 18 | 40 | 45.0% | 22 |
| organization | 5 | 13 | 38.5% | 8 |
| certificate | 5 | 20 | 25.0% | 15 |
| **mailbox** | **0** | **18** | **0%** | **18** |
| **linkedzone** | **0** | **12** | **0%** | **12** |
| **comment** | **0** | **3** | **0%** | **3** |
| simplehosting | 0 | 15 | 0% | 15 |
| template | 0 | 7 | 0% | 7 |
| **Total** | **72** | **208** | **34.6%** | **136** |

Existing 6 areas hold 153 endpoints (81 still missing). The 5 net-new areas (mailbox, linkedzone, comment, simplehosting, template) add 55 endpoints, all uncovered. Backfilling **only** the 6 existing areas tops out at 153/208 = **73.6%** — so reaching 90% now **requires** building new areas (see §3). Endpoint inventories for the three newly-discovered areas are in Appendix A.

---

## 2. Target: minimal set to reach >=90%

To reach **188 covered (90.4%)** implement **116 of the 136 missing endpoints** and **defer ~20** lowest-value ones. The split: backfill **all 81** gaps in the 6 existing areas (per the tables below), then build **35 of the 55** new-area endpoints (mailbox + linkedzone + comment + simplehosting + template), deferring the lowest-value plumbing (AXFR/TSIG, intermediate-PEM fetchers, org/customer deletes, the application catalog, template delete, etc.). Ordering within the build is **value (high → low), then effort (S → M)**, preferring read + free-write tools; purchase tools ship **gated, default-off**.

> The per-endpoint tables for the **6 existing areas** below are unchanged from the first pass and remain accurate (their paths were confirmed against the live RAML). The **3 newly-discovered areas** (mailbox, linkedzone, comment) are inventoried in Appendix A; simplehosting and template tables follow as before.

### Endpoints to IMPLEMENT — existing areas, grouped

Tier legend: R=read, W=write (free), P=purchase (gated).

#### domain (29 impl. missing → implement 29)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET …/{d}/tags | `list_domain_tags` | `gandi_domain_list_tags` | R | S |
| GET …/{d}/restore | `get_restore_info` | `gandi_domain_get_restore_info` | R | S |
| GET …/{d}/webredirs | `list_web_redirections` | `gandi_domain_list_web_redirections` | R | S |
| GET …/{d}/webredirs/{host} | `get_web_redirection` | `gandi_domain_get_web_redirection` | R | S |
| GET /v5/domain/transferin/{d}/available | `check_transferin_available` | `gandi_domain_check_transferin_available` | R | M |
| POST …/{d}/tags | `create_domain_tag` | `gandi_domain_create_tag` | W | S |
| PUT …/{d}/tags | `replace_domain_tags` | `gandi_domain_replace_tags` | W | S |
| PATCH …/{d}/tags | `update_domain_tags` | `gandi_domain_update_tags` | W | S |
| DELETE …/{d}/tags | `delete_domain_tags` | `gandi_domain_delete_tags` | W | S |
| DELETE …/{d}/webredirs/{host} | `delete_web_redirection` | `gandi_domain_delete_web_redirection` | W | S |
| POST …/{d}/webredirs | `create_web_redirection` | `gandi_domain_create_web_redirection` | W | M |
| PATCH …/{d}/webredirs/{host} | `update_web_redirection` | `gandi_domain_update_web_redirection` | W | M |
| POST …/{d}/livedns | `enable_domain_livedns` | `gandi_domain_enable_livedns` | W | S |
| POST …/{d}/restore | `restore_domain` | `gandi_domain_restore` | **P** | M |
| GET …/{d}/createstatus | `get_create_status` | `gandi_domain_get_create_status` | R | S |
| GET …/{d}/livedns | `get_domain_livedns` | `gandi_domain_get_livedns` | R | S |
| GET …/{d}/livedns/dnssec | `get_domain_livedns_dnssec` | `gandi_domain_get_livedns_dnssec` | R | S |
| GET /v5/domain/tlds | `list_tlds` | `gandi_domain_list_tlds` | R | S |
| GET /v5/domain/tlds/{name} | `get_tld` | `gandi_domain_get_tld` | R | S |
| POST …/{d}/livedns/dnssec | `activate_domain_livedns_dnssec` | `gandi_domain_activate_livedns_dnssec` | W | S |
| DELETE …/{d}/livedns/dnssec | `disable_domain_livedns_dnssec` | `gandi_domain_disable_livedns_dnssec` | W | S |
| PATCH …/{d}/reachability | `relaunch_reachability` | `gandi_domain_relaunch_reachability` | W | S |
| PUT …/{d}/contacts/owner | `update_owner_contact` | `gandi_domain_update_owner_contact` | **P** | M |
| PUT /v5/domain/transferin/{d} | `relaunch_transferin` | `gandi_domain_relaunch_transferin` | W | S |
| PUT /v5/domain/transferin/{d}/authinfo | `update_transferin_authinfo` | `gandi_domain_update_transferin_authinfo` | W | S |
| POST /v5/domain/transferin/{d}/foa | `resend_transferin_foa` | `gandi_domain_resend_transferin_foa` | W | S |
| PUT …/{d}/dnskeys | `replace_dnssec_keys` | `gandi_domain_replace_dnssec_keys` | W | S |
| POST …/{d}/claims | `accept_domain_claim` | `gandi_domain_accept_claim` | W | S |
| GET …/{d}/livedns/dnssec (read pair) | — | (covered above) | — | — |

(29 domain endpoints; the 2 excluded gaps `set_transfer_lock` / `transfer_out` are **not** here.)

#### livedns (22 missing → implement 17, defer 5)
<!-- count reconciled to §1 locked denominator (40 total / 18 covered); first-pass table below lists 21 — one low-value endpoint to be confirmed at build time -->

**Implement (high/medium value first):**
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET …/{fqdn}/snapshots | `livedns_list_snapshots` | `gandi_livedns_list_snapshots` | R | S |
| GET …/{fqdn}/snapshots/{id} | `livedns_get_snapshot` | `gandi_livedns_get_snapshot` | R | S |
| POST …/{fqdn}/snapshots | `livedns_create_snapshot` | `gandi_livedns_create_snapshot` | W | S |
| DELETE …/{fqdn}/snapshots/{id} | `livedns_delete_snapshot` | `gandi_livedns_delete_snapshot` | W | S |
| PATCH …/{fqdn}/snapshots/{id} | `livedns_update_snapshot` | `gandi_livedns_update_snapshot` | W | S |
| PATCH …/{fqdn}/keys/{id} | `livedns_restore_key` | `gandi_livedns_restore_dnssec_key` | W | S |
| PATCH …/{fqdn}/records/{name}/{type} | `livedns_update_record` | `gandi_livedns_update_record` | W | M |
| GET …/{fqdn}/keys/{id} | `livedns_get_key` | `gandi_livedns_get_dnssec_key` | R | S |
| GET /v5/livedns/nameservers/{fqdn} | `livedns_get_generic_nameservers` | `gandi_livedns_get_generic_nameservers` | R | S |
| POST …/{fqdn}/records/{name} | `livedns_create_named_record` | `gandi_livedns_create_named_record` | W | M |
| PUT …/{fqdn}/records/{name} | `livedns_replace_named_records` | `gandi_livedns_replace_named_records` | W | M |
| DELETE …/{fqdn}/records/{name} | `livedns_delete_named_records` | `gandi_livedns_delete_named_records` | W | S |
| POST …/{fqdn}/records/{name}/{type} | `livedns_create_typed_record` | `gandi_livedns_create_typed_record` | W | M |
| GET /v5/livedns/axfr/tsig | `livedns_list_tsig_keys` | `gandi_livedns_list_tsig_keys` | R | S |
| GET /v5/livedns/axfr/tsig/{id} | `livedns_get_tsig_key` | `gandi_livedns_get_tsig_key` | R | S |
| POST /v5/livedns/axfr/tsig | `livedns_create_tsig_key` | `gandi_livedns_create_tsig_key` | W | S |

**Defer (5, low value):** `get_tsig_key_config`, `list_axfr_slaves`, `add_axfr_slave`, `delete_axfr_slave`, plus one of the domain-scoped TSIG endpoints (`list/add/delete_domain_tsig_key` — defer the remaining low-value AXFR/TSIG plumbing).

#### email (5 missing → implement 3, defer 2)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET /v5/email/offers/{domain} | `email_get_offer` | `gandi_email_get_offer` | R | S |
| PATCH /v5/email/offers/{domain} | `email_update_offer` | `gandi_email_update_offer` | W | M |
| POST …/mailboxes/{domain}/renew | `email_renew_all_mailboxes` | `gandi_email_renew_all_mailboxes` | **P** | S |

**Defer (2, low value):** `email_get_migration`, `email_launch_migration`.

#### certificate (15 missing → implement 13, defer 2)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET …/issued-certs/{id}/crt | `cert_get_crt` | `gandi_cert_get_crt` | R | S |
| GET …/issued-certs/{id}/tags | `cert_list_tags` | `gandi_cert_list_tags` | R | S |
| GET /v5/certificate/packages | `cert_list_packages` | `gandi_cert_list_packages` | R | S |
| GET /v5/certificate/packages/{name} | `cert_get_package` | `gandi_cert_get_package` | R | S |
| POST /v5/certificate/dcv_params | `cert_get_dcv_params` | `gandi_cert_get_dcv_params` | R | M |
| POST …/issued-certs/{id}/dcv_params | `cert_get_dcv_params_for_cert` | `gandi_cert_get_cert_dcv_params` | R | M |
| PUT …/issued-certs/{id}/dcv | `cert_resend_dcv` | `gandi_cert_resend_dcv` | W | S |
| POST …/issued-certs/{id}/tags | `cert_add_tag` | `gandi_cert_add_tag` | W | S |
| PUT …/issued-certs/{id}/tags | `cert_replace_tags` | `gandi_cert_replace_tags` | W | S |
| PATCH …/issued-certs/{id}/tags | `cert_update_tags` | `gandi_cert_update_tags` | W | S |
| DELETE …/issued-certs/{id}/tags | `cert_delete_tags` | `gandi_cert_delete_tags` | W | S |
| PATCH …/issued-certs/{id}/dcv | `cert_update_dcv_method` | `gandi_cert_update_dcv_method` | W | M |
| PATCH …/issued-certs/{id} | `cert_update` | `gandi_cert_update` | W | M |

**Defer (2, low value):** `cert_get_intermediate_by_filename`, `cert_get_intermediate_by_type`.

#### organization (8 missing → implement 4, defer 4)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| POST …/organizations/{org_id}/customers | `create_customer` | `gandi_organization_create_customer` | W | M |
| PATCH …/organizations/{org_id}/customers/{id} | `update_customer` | `gandi_organization_update_customer` | W | M |
| PATCH …/organizations/{org_id} | `update_organization` | `gandi_organization_update_organization` | W | M |
| POST /v5/organization/access-tokens | `renew_access_token` | `gandi_organization_renew_access_token` | W | M |

**Defer (4, low value):** `create_organization`, `delete_organization`, `run_organization_action`, `delete_customer`.

#### simplehosting (15 missing → implement 13, defer 2)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET …/instances | `simplehosting_list_instances` | `gandi_simplehosting_list_instances` | R | S |
| GET …/instances/{id} | `simplehosting_get_instance` | `gandi_simplehosting_get_instance` | R | S |
| GET …/instances/{id}/vhosts | `simplehosting_list_vhosts` | `gandi_simplehosting_list_vhosts` | R | S |
| GET …/instances/{id}/vhosts/{fqdn} | `simplehosting_get_vhost` | `gandi_simplehosting_get_vhost` | R | S |
| GET …/instances/{id}/usage | `simplehosting_get_instance_usage` | `gandi_simplehosting_get_instance_usage` | R | S |
| DELETE …/instances/{id} | `simplehosting_delete_instance` | `gandi_simplehosting_delete_instance` | W | S |
| POST …/instances/{id}/action | `simplehosting_instance_action` | `gandi_simplehosting_perform_instance_action` | W | M |
| POST …/instances/{id}/vhosts | `simplehosting_create_vhost` | `gandi_simplehosting_create_vhost` | W | M |
| DELETE …/instances/{id}/vhosts/{fqdn} | `simplehosting_delete_vhost` | `gandi_simplehosting_delete_vhost` | W | S |
| PATCH …/instances/{id}/vhosts/{fqdn} | `simplehosting_update_vhost` | `gandi_simplehosting_update_vhost` | W | M |
| DELETE …/instances/{id}/vhosts/{fqdn}/cache | `simplehosting_purge_vhost_cache` | `gandi_simplehosting_purge_vhost_cache` | W | S |
| POST …/instances | `simplehosting_create_instance` | `gandi_simplehosting_create_instance` | **P** | M |
| PATCH …/instances/{id} | `simplehosting_update_instance` | `gandi_simplehosting_update_instance` | **P** | M |

**Defer (2, low value):** `simplehosting_list_applications`, `simplehosting_get_application`.

#### template (7 missing → implement 6, defer 1)
| Endpoint | Client method | Tool name | Tier | Effort |
|---|---|---|---|---|
| GET /v5/template/dispatch/{id} | `template_get_dispatch` | `gandi_template_get_dispatch` | R | S |
| POST /v5/template/templates/{id} | `template_apply_template` | `gandi_template_apply_template` | W | M |
| GET /v5/template/templates | `template_list_templates` | `gandi_template_list_templates` | R | S |
| GET /v5/template/templates/{id} | `template_get_template` | `gandi_template_get_template` | R | S |
| POST /v5/template/templates | `template_create_template` | `gandi_template_create_template` | W | M |
| PATCH /v5/template/templates/{id} | `template_update_template` | `gandi_template_update_template` | W | M |

**Defer (1, low value):** `template_delete_template`.

### Resulting coverage after the 116 additions

| | Covered | Denominator | % |
|---|---|---|---|
| Before | 72 | 208 | 34.6% |
| **After** | **188** | **208** | **90.4%** |

The ~20 deferred endpoints are all `low` value (livedns AXFR/TSIG plumbing, cert intermediate-PEM fetchers, org/customer deletes + create-org + run-action, email migration, simplehosting application catalog, template delete, plus a handful of low-value mailbox/linkedzone/comment calls). They can be picked up later without affecting the 90% gate.

---

## 3. Scoping call: five net-new areas required

**Reaching 90% requires building new areas — backfilling the existing 6 is not enough.** The locked denominator is 208 and 90% = 188 covered. The 6 existing areas hold only 153 endpoints, so even implementing **every** one of their 81 gaps reaches just **153/208 = 73.6%**. The remaining ~35 must come from the 5 net-new areas: **mailbox (18), linkedzone (12), comment (3), simplehosting (15), template (7)** = 55 endpoints.

**Recommendation:** land the existing-area backfill first (Phases 1–3 → 73.6%), then build the new areas in priority order (Phases 4–5). Highest-value new areas are **mailbox** (current product, high user value) and **linkedzone** (shared-DNS management); **comment** is tiny (3 endpoints, cheap to finish); **simplehosting** and **template** round out the count. Each new area is its own client-module + tools-module + cassette set in its own PR — do not entangle with existing-area work.

---

## 4. Sequencing (PRs / phases)

Each phase: add client methods in `clients/gandi.py` (path segments via `_seg()`), add tools in the matching `tools/*.py` with CLAUDE.md tagging/annotation conventions, write tools call `assert_readwrite`, purchase tools call `assert_readwrite` **then** `assert_purchases_allowed`, add `respx` unit tests + cassettes, regenerate the schema matrix (`tests/unit/test_tool_schema_matrix.py`), and run the consistency audit.

### Phase 1 — High-value read backfill (6 areas)  →  ~46%
- [ ] domain reads: `list_tags`, `get_restore_info`, `list_web_redirections`, `get_web_redirection`, `check_transferin_available`, `get_create_status`, `get_domain_livedns`, `get_domain_livedns_dnssec`, `list_tlds`, `get_tld`
- [ ] livedns reads: `list_snapshots`, `get_snapshot`, `get_key`, `get_generic_nameservers`, `list_tsig_keys`, `get_tsig_key`
- [ ] email read: `get_offer`
- [ ] certificate reads: `cert_get_crt`, `cert_list_tags`, `cert_list_packages`, `cert_get_package`, `cert_get_dcv_params`, `cert_get_dcv_params_for_cert`
- [ ] Tests: respx unit tests per method; matrix regen; `consistency-check audit --repo gandi-mcp`

### Phase 2 — Free-write backfill (6 areas)  →  ~66%
- [ ] domain writes: tag CRUD (`create_tag`/`replace_tags`/`update_tags`/`delete_tags`), webredir CRUD (`create`/`update`/`delete`), `enable_livedns`, `activate_livedns_dnssec`, `disable_livedns_dnssec`, `relaunch_reachability`, `replace_dnssec_keys`, `accept_claim`, transferin (`relaunch`/`update_authinfo`/`resend_foa`)
- [ ] livedns writes: snapshot CRUD (`create`/`update`/`delete`), `restore_dnssec_key`, record writes (`update_record`, `create_named_record`, `replace_named_records`, `delete_named_records`, `create_typed_record`), `create_tsig_key`
- [ ] email write: `update_offer`
- [ ] certificate writes: `cert_resend_dcv`, tag CRUD (`add`/`replace`/`update`/`delete`), `cert_update_dcv_method`, `cert_update`
- [ ] organization writes: `create_customer`, `update_customer`, `update_organization`, `renew_access_token`
- [ ] All write tools: `tags` include `"write"`, `annotations.readOnlyHint=False` (destructive deletes set `destructiveHint=True`), runtime `assert_readwrite`
- [ ] Tests + matrix regen + audit

### Phase 3 — Purchase tools, existing areas (gated, default-off)  →  ~73.6%
- [ ] domain: `restore_domain`, `update_owner_contact`
- [ ] email: `renew_all_mailboxes`
- [ ] Tags `{"write","purchase"}`; annotations `readOnlyHint=False, openWorldHint=True`; handlers call `assert_readwrite` then `assert_purchases_allowed`; hidden by both `mcp.disable(tags={"write"})` and `mcp.disable(tags={"purchase"})`
- [ ] Verify the three-tier gate tests (readonly / readwrite / readwrite+purchases) cover the new tools
- [ ] Tests + matrix regen + audit
- [ ] At this point all 81 existing-area gaps are closed → **153/208 = 73.6%**

### Phase 4 — New areas, batch 1: mailbox + linkedzone + comment  →  ~85%
- [ ] New modules `tools/mailbox.py`, `tools/linkedzone.py`, `tools/comment.py`; new client-method blocks; register in `server.py` with tags `{"gandi","mailbox"}` / `{"gandi","linkedzone"}` / `{"gandi","comment"}`
- [ ] mailbox reads: `mailbox_list_domains`, `mailbox_get_domain`, `mailbox_list_mailboxes`, `mailbox_get_mailbox`, `mailbox_list_forwards`, `mailbox_list_slots`, `mailbox_get_slot`, `mailbox_get_quotas`, `mailbox_list_products`
- [ ] mailbox writes: `mailbox_validate_domain`, `mailbox_update_mailbox`, `mailbox_delete_mailbox`, `mailbox_create_forward`, `mailbox_update_forward`, `mailbox_delete_forward`
- [ ] mailbox purchases (gated): `mailbox_create_mailbox` (POST /mailboxes), `mailbox_renew_mailbox` (POST /mailboxes/{email}/renew), `mailbox_buy_product` (POST /products)
- [ ] linkedzone reads: `linkedzone_list_domains`, `linkedzone_get_domain`, `linkedzone_list_zones`, `linkedzone_get_zone`, `linkedzone_list_tasks`, `linkedzone_get_task`
- [ ] linkedzone writes: `linkedzone_create_zone`, `linkedzone_update_zone`, `linkedzone_attach_domain` (POST /zones/{id}), `linkedzone_link_domains`, `linkedzone_unlink_domains`, `linkedzone_delete_zone`
- [ ] comment: `comment_get` (GET), `comment_set` (POST), `comment_delete` (DELETE) on `/v5/comment/comments/{id}`
- [ ] Same write/purchase gating rules; respx tests + cassettes per method; matrix regen + audit
- [ ] Reconcile mailbox vs. legacy email overlap in tool docstrings so an agent picks the right product

### Phase 5 — New areas, batch 2: simplehosting + template  →  90.4%
- [ ] New modules `tools/simplehosting.py`, `tools/template.py`; register in `server.py`
- [ ] simplehosting reads: `list_instances`, `get_instance`, `list_vhosts`, `get_vhost`, `get_instance_usage`
- [ ] simplehosting writes: `delete_instance`, `perform_instance_action`, `create_vhost`, `delete_vhost`, `update_vhost`, `purge_vhost_cache`
- [ ] simplehosting purchases (gated): `create_instance`, `update_instance`
- [ ] template reads: `list_templates`, `get_template`, `get_dispatch`
- [ ] template writes: `create_template`, `update_template`, `apply_template`
- [ ] Add `{"gandi","simplehosting"}` / `{"gandi","template"}` tags; same write/purchase gating rules
- [ ] Tests + matrix regen + audit  →  confirm **188/208 = 90.4%**

---

## 5. Risks & caveats

**Denominator source — no OpenAPI exists.** Gandi ships RAML-rendered HTML, not a machine-readable OpenAPI/Swagger doc. The 208 count was locked by counting `raml-method-verb` spans across the live docs on 2026-06-23; it will drift as Gandi edits the docs. Anyone revisiting this plan should re-pull and recount. There is no vendored spec in the repo to diff against — a follow-up could add a small `scripts/` fetcher that snapshots the RAML endpoint set so the matrix test can guard real coverage, not just self-consistency.

**Two CLAUDE.md "v5 gaps" contradict the live docs — reconcile before relying on either:**
1. `PATCH /v5/domain/domains/{domain}/status` (transfer-lock toggle) — CLAUDE.md says v5 has no write endpoint (only legacy XML-RPC `domain.status.lock/unlock`), yet the **live RAML renders this PATCH as a `/v5` method.** Verify against a real account before implementing. If genuinely live, it is a high-value write and CLAUDE.md's "v5 API gaps" section must be corrected.
2. `POST /v5/domain/domains/{domain}/transferout` — CLAUDE.md says v5 has no outbound-transfer endpoint (FOA-email driven), but the live RAML lists it. Same reconcile-first stance. Both are counted in the 208 denominator but flagged needs-verification, not auto-built.

**New auth path risk:** an XML-RPC transfer-lock fallback would give `GANDI_TOKEN` a second meaning (PAT for v5, apikey for XML-RPC). CLAUDE.md rejects this asymmetry — keep the server v5/Bearer-only; the live PATCH route above, if real, removes the need entirely.

**mailbox vs. email overlap:** the repo's `email` area (`/v5/email/*`) and the newly-found `mailbox` area (`/v5/mailbox/*`) are **different products**, not duplicates. Tool docstrings must disambiguate so an agent doesn't call the wrong one; both stay registered.

**Purchase-tool safety:** purchase tools across Phases 3–5 (domain restore/owner-change, email/mailbox renew, mailbox/simplehosting create) spend money or mutate external state. They MUST ship default-off behind `GANDI_MODE=readwrite` + `GANDI_ALLOW_PURCHASES=true`, double-gated by `mcp.disable` tags and runtime asserts. Don't let a purchase tool slip into the `"write"`-only tier.

**Matrix guard:** `tests/unit/test_tool_schema_matrix.py` generates and guards the tool/schema coverage matrix — every phase must regenerate it or CI drift-checks fail. Re-record cassettes (`make refresh-cassettes`) whenever a new request shape lands; CI checks cassette freshness.

**Deferred (~20 low-value) endpoints** left unimplemented: livedns AXFR-slave + remaining TSIG plumbing, cert intermediate-PEM fetchers, org create/delete-org + run-action + delete-customer, email migration get/launch, simplehosting application catalog, template delete, and the lowest-value mailbox/linkedzone calls. None block 90%; schedule as a later cleanup PR if/when load-bearing.

---

## Appendix A — newly-discovered areas (locked from live RAML, 2026-06-23)

These three areas had **zero** coverage and were absent from the first enumeration. Paths are the live `/v5` resources; tier per HTTP method (GET=read, mutation=write, paid create/renew=purchase). Param segments shown with `{}`.

### mailbox (`/v5/mailbox`) — 18 endpoints
| Method | Path | Tier |
|---|---|---|
| GET | `/v5/mailbox/domains` | read |
| GET | `/v5/mailbox/domains/{domain}` | read |
| POST | `/v5/mailbox/domains/{domain}/validate` | write |
| GET | `/v5/mailbox/mailboxes` | read |
| POST | `/v5/mailbox/mailboxes` | purchase |
| GET | `/v5/mailbox/mailboxes/{email}` | read |
| PATCH | `/v5/mailbox/mailboxes/{email}` | write |
| DELETE | `/v5/mailbox/mailboxes/{email}` | write |
| POST | `/v5/mailbox/mailboxes/{email}/renew` | purchase |
| GET | `/v5/mailbox/forwards` | read |
| POST | `/v5/mailbox/forwards` | write |
| PUT | `/v5/mailbox/forwards` | write |
| PUT | `/v5/mailbox/forwards/{source}` | write |
| DELETE | `/v5/mailbox/forwards` | write |
| DELETE | `/v5/mailbox/forwards/{source}` | write |
| GET | `/v5/mailbox/slots` | read |
| GET | `/v5/mailbox/slots/{slot_id}` | read |
| GET | `/v5/mailbox/quotas` | read |
| GET | `/v5/mailbox/products` | read |
| POST | `/v5/mailbox/products` | purchase |

*(20 anchors render; 18 distinct verb-spans — the forwards `PUT`/`DELETE` with and without `{source}` collapse in the docs. Confirm exact request shapes when recording cassettes.)*

### linkedzone (`/v5/linkedzone`) — 12 endpoints
| Method | Path | Tier |
|---|---|---|
| GET | `/v5/linkedzone/domains` | read |
| GET | `/v5/linkedzone/domains/{domain}` | read |
| GET | `/v5/linkedzone/zones` | read |
| POST | `/v5/linkedzone/zones` | write |
| GET | `/v5/linkedzone/zones/{zone_id}` | read |
| POST | `/v5/linkedzone/zones/{zone_id}` | write |
| PATCH | `/v5/linkedzone/zones/{zone_id}` | write |
| DELETE | `/v5/linkedzone/zones/{zone_id}` | write |
| PATCH | `/v5/linkedzone/zones/{zone_id}/link/domains` | write |
| PATCH | `/v5/linkedzone/unlink/domains` | write |
| GET | `/v5/linkedzone/tasks` | read |
| GET | `/v5/linkedzone/tasks/{task_id}` | read |

### comment (`/v5/comment`) — 3 endpoints
| Method | Path | Tier |
|---|---|---|
| GET | `/v5/comment/comments/{id}` | read |
| POST | `/v5/comment/comments/{id}` | write |
| DELETE | `/v5/comment/comments/{id}` | write |