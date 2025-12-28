# Platform Critical Gaps Implementation Plan (Revised)

This plan tightens rollout strategy, wiring, and enforcement scope to avoid outages.

## Guiding Principles

- Ship safe defaults first; expand policy/enforcement after verifying impact.
- Prefer dual-stack compatibility during migrations (HS256 -> RS/ES).
- Avoid template files unless they are actually applied by code.
- Gate enforcement to subscription-scoped endpoints before global gating.

## Priority Order (Adjusted)

1. JWKS Endpoint and JWT migration
2. TLS automation (cert-manager integration)
3. Secret rotation jobs (depends on JWKS)
4. NetworkPolicies (expand existing policy)
5. Grace period enforcement (subscription-scoped)
6. Backup/restore (v0 end-to-end)

## Workstreams

### 1) JWKS Endpoint and JWT Migration

Goal: Support asymmetric signing with clean key rotation and OIDC discovery.

Key decisions:
- Support HS256 and RS/ES in parallel during rollout.
- Keep old keys for a verification grace window.
- `kid` lookup must be mandatory for asymmetric verification.

Implementation outline:
- Add asymmetric key settings (private/public, key id, issuer, audience).
- Add KeyManager for JWK generation and key rotation metadata.
- Update JWTService to:
  - Add `iss` and `aud` to tokens.
  - Sign with asymmetric key when configured, else HS256.
  - Verify with matching `kid`; fallback to previous keys.
  - Support HS256 verification during migration only.
- Add `/.well-known/jwks.json` and `/.well-known/openid-configuration`.
- Register OIDC endpoints at app root (not `/api/v1`).

Acceptance criteria:
- Tokens signed with RS/ES validate using JWKS.
- Existing HS256 tokens remain valid during migration window.
- `iss` and `aud` are present in all new tokens.

### 2) TLS Automation (cert-manager)

Goal: Automate cert provisioning for tenant ingress.

Implementation outline:
- Add TLS settings (issuer type, email, namespace).
- In Kubernetes adapter:
  - Create ClusterIssuer if missing (Let's Encrypt + self-signed for dev).
  - Add cert-manager annotations to ingress.
  - Add TLS blocks to ingress spec.

Acceptance criteria:
- New tenant ingress provisions certs without manual steps.
- Dev mode can use self-signed issuer.

### 3) Secret Rotation Jobs

Goal: Scheduled rotation with zero-downtime grace windows.

Implementation outline:
- Add Celery tasks:
  - Rotate JWT signing keys (writes to Vault, updates KeyManager).
  - Warn on expiring API keys.
  - Rotate tenant DB credentials (requires coordinated rollout).
- Add beat schedule and rotation settings.
- Ensure JWT verification supports multiple active keys.

Acceptance criteria:
- New keys rotate without breaking auth.
- Rotation schedules are configurable and observable.

### 4) NetworkPolicies (Full Model)

Goal: Strict tenant isolation with explicit allowlists.

Implementation outline:
- Extend existing deny-all ingress (already implemented).
- Add deny-all egress and explicit allowlist:
  - DNS (kube-dns)
  - Ingress controller -> tenant service
  - Tenant service -> tenant DB
  - Tenant service -> platform APIs
  - Tenant service -> observability endpoints
  - Intra-namespace pod-to-pod
- Add network policy settings for allowed namespaces and CIDRs.

Acceptance criteria:
- Default cross-tenant traffic blocked.
- Required service paths are explicitly permitted.

### 5) Grace Period Enforcement

Goal: Enforce payment grace periods without blocking admin/ops flows.

Implementation outline:
- Add scheduled enforcement task:
  - Identify subscriptions beyond grace period.
  - Transition to SUSPENDED or PAST_DUE.
  - Trigger dunning escalation.
- Add enforcement only on subscription-scoped endpoints (billing/licensing).
- Return 402 for gated endpoints with grace period metadata.

Acceptance criteria:
- Overdue subscriptions are effectively gated on billing/licensing routes.
- Admin and operational endpoints remain accessible.

### 6) Backup/Restore (v0)

Goal: Reliable full backup + restore with a tested runbook.

Implementation outline:
- Implement a basic database exporter/importer (pg_dump/pg_restore).
- Store backups in object storage (MinIO).
- Add CLI or internal endpoint to trigger a backup and restore.
- Write a restore runbook and validate once end-to-end.

Acceptance criteria:
- One tenant backup + restore succeeds end-to-end.
- Runbook documents steps and validation.

## Ticket Plan

PCG-01: Add auth settings for asymmetric JWT + issuer/audience.  
PCG-02: Implement KeyManager + JWKS generation.  
PCG-03: Update JWTService signing/verification with dual-stack migration.  
PCG-04: Add OIDC discovery + JWKS endpoints, register at root.  
PCG-05: Add TLS settings and cert-manager integration in K8s adapter.  
PCG-06: Add secret rotation tasks + beat schedule + settings.  
PCG-07: Expand NetworkPolicies with deny-egress + allowlists.  
PCG-08: Add grace period enforcement task + scoped middleware gating.  
PCG-09: Implement v0 backup exporter/importer + runbook.  

## Dependencies

- PCG-03 depends on PCG-01/02.  
- PCG-06 depends on PCG-03.  
- PCG-08 depends on billing/subscription status model choices.  

## Risks and Mitigations

- Auth breakage during JWKS rollout: mitigate with HS256 fallback window.
- NetworkPolicy regressions: start with DNS and platform allowlists, log drops.
- TLS automation failures: support self-signed issuer for dev/test.

