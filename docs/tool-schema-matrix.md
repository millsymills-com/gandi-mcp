# Tool / schema coverage matrix

<!-- GENERATED FILE — do not edit by hand.
     Regenerate: uv run python tests/unit/test_tool_schema_matrix.py
     Guarded by: tests/unit/test_tool_schema_matrix.py -->

Every MCP tool this server exposes, mapped to its safety tier, MCP annotation
hints, the `GandiClient` method it calls, and the Gandi v5 endpoint behind that
method. `tests/unit/test_tool_schema_matrix.py` fails if this table drifts from
the registered tool surface.

Tiers follow the three-tier safety model: **read** (always visible), **write**
(needs `GANDI_MODE=readwrite`), **purchase** (also needs `GANDI_ALLOW_PURCHASES=true`).
Destructive and open-world columns reflect the tool's MCP annotation hints.

**146 tools** — 64 read, 74 write, 8 purchase.

| Area | Tier | Tool | Destructive | Open-world | Client method | Gandi v5 endpoint |
|------|------|------|:-----------:|:----------:|---------------|-------------------|
| billing | read | `gandi_billing_get_info` | no | no | `get_billing_info` | `GET /v5/billing/info` |
| billing | read | `gandi_billing_get_info_for_org` | no | no | `get_billing_info_for_org` | `GET /v5/billing/info/{sharing_id}` |
| billing | read | `gandi_billing_get_price_catalog` | no | no | `get_price_catalog` | `GET /v5/billing/price/{product_type}` |
| certificate | read | `gandi_cert_get` | no | no | `cert_get` | `GET /v5/certificate/issued-certs/{cert_id}` |
| certificate | read | `gandi_cert_get_package` | no | no | `cert_get_package` | `GET /v5/certificate/packages/{name}` |
| certificate | read | `gandi_cert_list` | no | no | `cert_list` | `GET /v5/certificate/issued-certs` |
| certificate | read | `gandi_cert_list_packages` | no | no | `cert_list_packages` | `GET /v5/certificate/packages` |
| certificate | read | `gandi_cert_list_tags` | no | no | `cert_list_tags` | `GET /v5/certificate/issued-certs/{cert_id}/tags` |
| certificate | write | `gandi_cert_add_tag` | no | no | `cert_add_tag` | `POST /v5/certificate/issued-certs/{cert_id}/tags` |
| certificate | write | `gandi_cert_delete_tags` | yes | no | `cert_delete_tags` | `DELETE /v5/certificate/issued-certs/{cert_id}/tags` |
| certificate | write | `gandi_cert_replace_tags` | yes | no | `cert_replace_tags` | `PUT /v5/certificate/issued-certs/{cert_id}/tags` |
| certificate | write | `gandi_cert_revoke` | yes | no | `cert_revoke` | `DELETE /v5/certificate/issued-certs/{cert_id}` |
| certificate | write | `gandi_cert_update_tags` | no | no | `cert_update_tags` | `PATCH /v5/certificate/issued-certs/{cert_id}/tags` |
| certificate | purchase | `gandi_cert_issue` | no | yes | `cert_issue` | `POST /v5/certificate/issued-certs` |
| certificate | purchase | `gandi_cert_renew` | no | yes | `cert_renew` | `POST /v5/certificate/issued-certs/{cert_id}/renew` |
| comment | read | `gandi_comment_get` | no | no | `get_comment` | `GET /v5/comment/comments/{comment_id}` |
| comment | write | `gandi_comment_delete` | yes | no | `delete_comment` | `DELETE /v5/comment/comments/{comment_id}` |
| comment | write | `gandi_comment_set` | no | no | `set_comment` | `POST /v5/comment/comments/{comment_id}` |
| domain | read | `gandi_domain_check_availability` | no | no | `check_availability` | `GET /v5/domain/check` |
| domain | read | `gandi_domain_check_transferin_available` | no | no | `check_transferin_available` | `GET /v5/domain/transferin/{fqdn}/available` |
| domain | read | `gandi_domain_get_claims` | no | no | `get_domain_claims` | `GET /v5/domain/domains/{fqdn}/claims` |
| domain | read | `gandi_domain_get_contacts` | no | no | `get_domain_contacts` | `GET /v5/domain/domains/{fqdn}/contacts` |
| domain | read | `gandi_domain_get_create_status` | no | no | `get_create_status` | `GET /v5/domain/domains/{fqdn}/createstatus` |
| domain | read | `gandi_domain_get_domain` | no | no | `get_domain` | `GET /v5/domain/domains/{fqdn}` |
| domain | read | `gandi_domain_get_glue_record` | no | no | `get_glue_record` | `GET /v5/domain/domains/{fqdn}/hosts/{name}` |
| domain | read | `gandi_domain_get_livedns` | no | no | `get_domain_livedns` | `GET /v5/domain/domains/{fqdn}/livedns` |
| domain | read | `gandi_domain_get_livedns_dnssec` | no | no | `get_domain_livedns_dnssec` | `GET /v5/domain/domains/{fqdn}/livedns/dnssec` |
| domain | read | `gandi_domain_get_nameservers` | no | no | `get_nameservers` | `GET /v5/domain/domains/{fqdn}/nameservers` |
| domain | read | `gandi_domain_get_ownership_change_status` | no | no | `get_ownership_change_status` | `GET /v5/domain/changeowner/{fqdn}` |
| domain | read | `gandi_domain_get_renew_info` | no | no | `get_renew_info` | `GET /v5/domain/domains/{fqdn}/renew` |
| domain | read | `gandi_domain_get_restore_info` | no | no | `get_restore_info` | `GET /v5/domain/domains/{fqdn}/restore` |
| domain | read | `gandi_domain_get_status` | no | no | `get_domain` | `GET /v5/domain/domains/{fqdn}` |
| domain | read | `gandi_domain_get_tld` | no | no | `get_tld` | `GET /v5/domain/tlds/{name}` |
| domain | read | `gandi_domain_get_transferin_info` | no | no | `get_transferin_info` | `GET /v5/domain/transferin/{fqdn}` |
| domain | read | `gandi_domain_get_web_redirection` | no | no | `get_web_redirection` | `GET /v5/domain/domains/{fqdn}/webredirs/{host}` |
| domain | read | `gandi_domain_list_dnssec_keys` | no | no | `list_dnssec_keys` | `GET /v5/domain/domains/{fqdn}/dnskeys` |
| domain | read | `gandi_domain_list_domains` | no | no | `list_domains` | `GET /v5/domain/domains` |
| domain | read | `gandi_domain_list_glue_records` | no | no | `list_glue_records` | `GET /v5/domain/domains/{fqdn}/hosts` |
| domain | read | `gandi_domain_list_tags` | no | no | `list_domain_tags` | `GET /v5/domain/domains/{fqdn}/tags` |
| domain | read | `gandi_domain_list_tlds` | no | no | `list_tlds` | `GET /v5/domain/tlds` |
| domain | read | `gandi_domain_list_web_redirections` | no | no | `list_web_redirections` | `GET /v5/domain/domains/{fqdn}/webredirs` |
| domain | write | `gandi_domain_accept_claim` | no | no | `accept_claim` | `POST /v5/domain/domains/{fqdn}/claims` |
| domain | write | `gandi_domain_activate_livedns_dnssec` | no | no | `activate_domain_livedns_dnssec` | `POST /v5/domain/domains/{fqdn}/livedns/dnssec` |
| domain | write | `gandi_domain_create_dnssec_key` | no | no | `create_dnssec_key` | `POST /v5/domain/domains/{fqdn}/dnskeys` |
| domain | write | `gandi_domain_create_glue_record` | no | no | `create_glue_record` | `POST /v5/domain/domains/{fqdn}/hosts` |
| domain | write | `gandi_domain_create_tag` | no | no | `create_domain_tag` | `POST /v5/domain/domains/{fqdn}/tags` |
| domain | write | `gandi_domain_create_web_redirection` | no | no | `create_web_redirection` | `POST /v5/domain/domains/{fqdn}/webredirs` |
| domain | write | `gandi_domain_delete` | yes | no | `delete_domain` | `DELETE /v5/domain/domains/{fqdn}` |
| domain | write | `gandi_domain_delete_dnssec_key` | yes | no | `delete_dnssec_key` | `DELETE /v5/domain/domains/{fqdn}/dnskeys/{key_id}` |
| domain | write | `gandi_domain_delete_glue_record` | yes | no | `delete_glue_record` | `DELETE /v5/domain/domains/{fqdn}/hosts/{name}` |
| domain | write | `gandi_domain_delete_tags` | yes | no | `delete_domain_tags` | `DELETE /v5/domain/domains/{fqdn}/tags` |
| domain | write | `gandi_domain_delete_web_redirection` | yes | no | `delete_web_redirection` | `DELETE /v5/domain/domains/{fqdn}/webredirs/{host}` |
| domain | write | `gandi_domain_disable_livedns_dnssec` | yes | no | `disable_domain_livedns_dnssec` | `DELETE /v5/domain/domains/{fqdn}/livedns/dnssec` |
| domain | write | `gandi_domain_enable_livedns` | no | no | `enable_domain_livedns` | `POST /v5/domain/domains/{fqdn}/livedns` |
| domain | write | `gandi_domain_initiate_ownership_change` | no | no | `initiate_ownership_change` | `POST /v5/domain/changeowner/{fqdn}` |
| domain | write | `gandi_domain_relaunch_reachability` | no | no | `relaunch_reachability` | `PATCH /v5/domain/domains/{fqdn}/reachability` |
| domain | write | `gandi_domain_relaunch_transferin` | no | no | `relaunch_transferin` | `PUT /v5/domain/transferin/{fqdn}` |
| domain | write | `gandi_domain_replace_dnssec_keys` | yes | no | `replace_dnssec_keys` | `PUT /v5/domain/domains/{fqdn}/dnskeys` |
| domain | write | `gandi_domain_replace_tags` | yes | no | `replace_domain_tags` | `PUT /v5/domain/domains/{fqdn}/tags` |
| domain | write | `gandi_domain_resend_foa` | no | no | `resend_foa` | `POST /v5/domain/changeowner/{fqdn}/foa` |
| domain | write | `gandi_domain_resend_transferin_foa` | no | no | `resend_transferin_foa` | `POST /v5/domain/transferin/{fqdn}/foa` |
| domain | write | `gandi_domain_reset_authinfo` | no | no | `reset_authinfo` | `PUT /v5/domain/domains/{fqdn}/authinfo` |
| domain | write | `gandi_domain_set_autorenew` | no | no | `set_autorenew` | `PATCH /v5/domain/domains/{fqdn}/autorenew` |
| domain | write | `gandi_domain_set_nameservers` | no | no | `set_nameservers` | `PUT /v5/domain/domains/{fqdn}/nameservers` |
| domain | write | `gandi_domain_update_contacts` | no | no | `update_domain_contacts` | `PATCH /v5/domain/domains/{fqdn}/contacts` |
| domain | write | `gandi_domain_update_glue_record` | no | no | `update_glue_record` | `PUT /v5/domain/domains/{fqdn}/hosts/{name}` |
| domain | write | `gandi_domain_update_tags` | no | no | `update_domain_tags` | `PATCH /v5/domain/domains/{fqdn}/tags` |
| domain | write | `gandi_domain_update_transferin_authinfo` | no | no | `update_transferin_authinfo` | `PUT /v5/domain/transferin/{fqdn}/authinfo` |
| domain | write | `gandi_domain_update_web_redirection` | no | no | `update_web_redirection` | `PATCH /v5/domain/domains/{fqdn}/webredirs/{host}` |
| domain | purchase | `gandi_domain_register` | no | yes | `register_domain` | `POST /v5/domain/domains` |
| domain | purchase | `gandi_domain_renew` | no | yes | `renew_domain` | `POST /v5/domain/domains/{fqdn}/renew` |
| domain | purchase | `gandi_domain_transfer_in` | no | yes | `transfer_in` | `POST /v5/domain/transferin/{fqdn}` |
| email | read | `gandi_email_get_mailbox` | no | no | `email_get_mailbox` | `GET /v5/email/mailboxes/{domain}/{mailbox_id}` |
| email | read | `gandi_email_get_offer` | no | no | `email_get_offer` | `GET /v5/email/offers/{domain}` |
| email | read | `gandi_email_get_slot` | no | no | `email_get_slot` | `GET /v5/email/slots/{domain}/{slot_id}` |
| email | read | `gandi_email_list_forwards` | no | no | `email_list_forwards` | `GET /v5/email/forwards/{domain}` |
| email | read | `gandi_email_list_mailboxes` | no | no | `email_list_mailboxes` | `GET /v5/email/mailboxes/{domain}` |
| email | read | `gandi_email_list_slots` | no | no | `email_list_slots` | `GET /v5/email/slots/{domain}` |
| email | write | `gandi_email_create_forward` | no | no | `email_create_forward` | `POST /v5/email/forwards/{domain}` |
| email | write | `gandi_email_delete_forward` | yes | no | `email_delete_forward` | `DELETE /v5/email/forwards/{domain}/{source}` |
| email | write | `gandi_email_delete_mailbox` | yes | no | `email_delete_mailbox` | `DELETE /v5/email/mailboxes/{domain}/{mailbox_id}` |
| email | write | `gandi_email_purge_mailbox` | yes | no | `email_purge_mailbox` | `DELETE /v5/email/mailboxes/{domain}/{mailbox_id}/contents` |
| email | write | `gandi_email_refund_slot` | yes | no | `email_refund_slot` | `DELETE /v5/email/slots/{domain}/{slot_id}` |
| email | write | `gandi_email_update_forward` | no | no | `email_update_forward` | `PUT /v5/email/forwards/{domain}/{source}` |
| email | write | `gandi_email_update_mailbox` | no | no | `email_update_mailbox` | `PATCH /v5/email/mailboxes/{domain}/{mailbox_id}` |
| email | purchase | `gandi_email_create_mailbox` | no | yes | `email_create_mailbox` | `POST /v5/email/mailboxes/{domain}` |
| email | purchase | `gandi_email_create_slot` | no | yes | `email_create_slot` | `POST /v5/email/slots/{domain}` |
| email | purchase | `gandi_email_renew_mailbox` | no | yes | `email_renew_mailbox` | `POST /v5/email/mailboxes/{domain}/{email}/renew` |
| linkedzone | read | `gandi_linkedzone_get_domain` | no | no | `linkedzone_get_domain` | `GET /v5/linkedzone/domains/{domain}` |
| linkedzone | read | `gandi_linkedzone_get_task` | no | no | `linkedzone_get_task` | `GET /v5/linkedzone/tasks/{task_id}` |
| linkedzone | read | `gandi_linkedzone_get_zone` | no | no | `linkedzone_get_zone` | `GET /v5/linkedzone/zones/{zone_id}` |
| linkedzone | read | `gandi_linkedzone_list_domains` | no | no | `linkedzone_list_domains` | `GET /v5/linkedzone/domains` |
| linkedzone | read | `gandi_linkedzone_list_tasks` | no | no | `linkedzone_list_tasks` | `GET /v5/linkedzone/tasks` |
| linkedzone | read | `gandi_linkedzone_list_zones` | no | no | `linkedzone_list_zones` | `GET /v5/linkedzone/zones` |
| linkedzone | write | `gandi_linkedzone_attach_domain` | no | no | `linkedzone_attach_domain` | `POST /v5/linkedzone/zones/{zone_id}` |
| linkedzone | write | `gandi_linkedzone_create_zone` | no | no | `linkedzone_create_zone` | `POST /v5/linkedzone/zones` |
| linkedzone | write | `gandi_linkedzone_delete_zone` | yes | no | `linkedzone_delete_zone` | `DELETE /v5/linkedzone/zones/{zone_id}` |
| linkedzone | write | `gandi_linkedzone_link_domains` | no | no | `linkedzone_link_domains` | `PATCH /v5/linkedzone/zones/{zone_id}/link/domains` |
| linkedzone | write | `gandi_linkedzone_unlink_domains` | yes | no | `linkedzone_unlink_domains` | `PATCH /v5/linkedzone/unlink/domains` |
| linkedzone | write | `gandi_linkedzone_update_zone` | no | no | `linkedzone_update_zone` | `PATCH /v5/linkedzone/zones/{zone_id}` |
| livedns | read | `gandi_livedns_get_dnssec_key` | no | no | `livedns_get_key` | `GET /v5/livedns/domains/{fqdn}/keys/{key_id}` |
| livedns | read | `gandi_livedns_get_domain` | no | no | `livedns_get_domain` | `GET /v5/livedns/domains/{fqdn}` |
| livedns | read | `gandi_livedns_get_generic_nameservers` | no | no | `livedns_get_generic_nameservers` | `GET /v5/livedns/nameservers/{fqdn}` |
| livedns | read | `gandi_livedns_get_snapshot` | no | no | `livedns_get_snapshot` | `GET /v5/livedns/domains/{fqdn}/snapshots/{snapshot_id}` |
| livedns | read | `gandi_livedns_get_tsig_key` | no | no | `livedns_get_tsig_key` | `GET /v5/livedns/axfr/tsig/{tsig_id}` |
| livedns | read | `gandi_livedns_list_dnssec_keys` | no | no | `livedns_list_keys` | `GET /v5/livedns/domains/{fqdn}/keys` |
| livedns | read | `gandi_livedns_list_domains` | no | no | `livedns_list_domains` | `GET /v5/livedns/domains` |
| livedns | read | `gandi_livedns_list_nameservers` | no | no | `livedns_list_nameservers` | `GET /v5/livedns/domains/{fqdn}/nameservers` |
| livedns | read | `gandi_livedns_list_records` | no | no | `livedns_list_records` | `GET /v5/livedns/domains/{fqdn}/records[/{name}[/{rrset_type}]]` |
| livedns | read | `gandi_livedns_list_rrtypes` | no | no | `livedns_list_rrtypes` | `GET /v5/livedns/dns/rrtypes` |
| livedns | read | `gandi_livedns_list_snapshots` | no | no | `livedns_list_snapshots` | `GET /v5/livedns/domains/{fqdn}/snapshots` |
| livedns | read | `gandi_livedns_list_tsig_keys` | no | no | `livedns_list_tsig_keys` | `GET /v5/livedns/axfr/tsig` |
| livedns | write | `gandi_livedns_add_domain` | no | no | `livedns_add_domain` | `POST /v5/livedns/domains` |
| livedns | write | `gandi_livedns_create_dnssec_key` | no | no | `livedns_create_key` | `POST /v5/livedns/domains/{fqdn}/keys` |
| livedns | write | `gandi_livedns_create_named_record` | no | no | `livedns_create_named_record` | `POST /v5/livedns/domains/{fqdn}/records/{name}` |
| livedns | write | `gandi_livedns_create_record` | no | no | `livedns_create_record` | `POST /v5/livedns/domains/{fqdn}/records` |
| livedns | write | `gandi_livedns_create_snapshot` | no | no | `livedns_create_snapshot` | `POST /v5/livedns/domains/{fqdn}/snapshots` |
| livedns | write | `gandi_livedns_create_tsig_key` | no | no | `livedns_create_tsig_key` | `POST /v5/livedns/axfr/tsig` |
| livedns | write | `gandi_livedns_create_typed_record` | no | no | `livedns_create_typed_record` | `POST /v5/livedns/domains/{fqdn}/records/{name}/{rrset_type}` |
| livedns | write | `gandi_livedns_delete_all_records` | yes | no | `livedns_delete_all_records` | `DELETE /v5/livedns/domains/{fqdn}/records` |
| livedns | write | `gandi_livedns_delete_dnssec_key` | yes | no | `livedns_delete_key` | `DELETE /v5/livedns/domains/{fqdn}/keys/{key_id}` |
| livedns | write | `gandi_livedns_delete_named_records` | yes | no | `livedns_delete_named_records` | `DELETE /v5/livedns/domains/{fqdn}/records/{name}` |
| livedns | write | `gandi_livedns_delete_record` | yes | no | `livedns_delete_record` | `DELETE /v5/livedns/domains/{fqdn}/records/{name}/{rrset_type}` |
| livedns | write | `gandi_livedns_delete_snapshot` | yes | no | `livedns_delete_snapshot` | `DELETE /v5/livedns/domains/{fqdn}/snapshots/{snapshot_id}` |
| livedns | write | `gandi_livedns_replace_named_records` | yes | no | `livedns_replace_named_records` | `PUT /v5/livedns/domains/{fqdn}/records/{name}` |
| livedns | write | `gandi_livedns_replace_record` | no | no | `livedns_replace_record` | `PUT /v5/livedns/domains/{fqdn}/records/{name}/{rrset_type}` |
| livedns | write | `gandi_livedns_replace_zone` | yes | no | `livedns_replace_zone` | `PUT /v5/livedns/domains/{fqdn}/records` |
| livedns | write | `gandi_livedns_restore_dnssec_key` | no | no | `livedns_restore_key` | `PATCH /v5/livedns/domains/{fqdn}/keys/{key_id}` |
| livedns | write | `gandi_livedns_update_domain` | no | no | `livedns_patch_domain` | `PATCH /v5/livedns/domains/{fqdn}` |
| livedns | write | `gandi_livedns_update_record` | no | no | `livedns_update_record` | `PATCH /v5/livedns/domains/{fqdn}/records/{name}/{rrset_type}` |
| livedns | write | `gandi_livedns_update_snapshot` | no | no | `livedns_update_snapshot` | `PATCH /v5/livedns/domains/{fqdn}/snapshots/{snapshot_id}` |
| organization | read | `gandi_org_get_customer` | no | no | `get_customer` | `GET /v5/organization/organizations/{org_id}/customers/{customer_id}` |
| organization | read | `gandi_org_get_organization` | no | no | `get_organization` | `GET /v5/organization/organizations/{org_id}` |
| organization | read | `gandi_org_get_user_info` | no | no | `get_user_info` | `GET /v5/organization/user-info` |
| organization | read | `gandi_org_list_customers` | no | no | `list_customers` | `GET /v5/organization/organizations/{org_id}/customers` |
| organization | read | `gandi_org_list_organizations` | no | no | `list_organizations` | `GET /v5/organization/organizations` |
| organization | write | `gandi_org_create_customer` | no | no | `create_customer` | `POST /v5/organization/organizations/{org_id}/customers` |
| organization | write | `gandi_org_renew_access_token` | no | no | `renew_access_token` | `POST /v5/organization/access-tokens` |
| organization | write | `gandi_org_update_customer` | no | no | `update_customer` | `PATCH /v5/organization/organizations/{org_id}/customers/{customer_id}` |
| organization | write | `gandi_org_update_organization` | no | no | `update_organization` | `PATCH /v5/organization/organizations/{org_id}` |
| template | read | `gandi_template_get_dispatch` | no | no | `template_get_dispatch` | `GET /v5/template/dispatch/{dispatch_id}` |
| template | read | `gandi_template_get_template` | no | no | `template_get_template` | `GET /v5/template/templates/{template_id}` |
| template | read | `gandi_template_list_templates` | no | no | `template_list_templates` | `GET /v5/template/templates` |
| template | write | `gandi_template_apply_template` | yes | no | `template_apply_template` | `POST /v5/template/templates/{template_id}` |
| template | write | `gandi_template_create_template` | no | no | `template_create_template` | `POST /v5/template/templates` |
| template | write | `gandi_template_update_template` | no | no | `template_update_template` | `PATCH /v5/template/templates/{template_id}` |
