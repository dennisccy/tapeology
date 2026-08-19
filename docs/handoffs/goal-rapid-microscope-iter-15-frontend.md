# goal-rapid-microscope-iter-15 Frontend Handoff

**Phase:** goal-rapid-microscope-iter-15
**Date:** 2026-08-19
**Agent:** developer
**Status:** complete

## What Was Built

No new section, no new page, no new nav entry. The four already-shipped Rapid-Microscope panels on
`/desk` become fully honest and four small defects are fixed — all inside their already-registered
homes.

- **Microscope Readiness** gains a new "Sealed Tranche (Aggregate Only)" block, rendered directly
  below the existing Corpus Totals table: `sealed_tranche.shard_count`, `sealed_tranche.
  symbol_days`, a per-universe breakdown table (`universe_id → {shard_count, symbol_days}`, or "No
  sealed shards recorded." when empty), and `joinable_corpus.withheld_excluded` as one more labeled
  count. Every value is served verbatim by the already-shipped, unchanged `GET /research/desk/micro/
  readiness` — this is a pure disclosure-completeness fix (the frontend `MicroReadinessResponse`
  type silently dropped both fields since iteration 10 registered them), not a new backend
  capability. AGGREGATE ONLY: no symbol, session date, dataset id, raw checksum, or per-shard
  `exposure_state` for a withheld shard appears anywhere in the new markup — the same opaque-pool
  discipline the endpoint itself already enforces server-side.
- **Scout Ledger**'s family header now shows `family_root_id` beside the existing `family_id`/
  `variants_tried` text (the field was already on `ScoutFamily` and already fetched — no new fetch,
  no new type).
- **Walk-Forward**'s empty-sequences state now reads "No walk-forward sequences run." instead of
  the reused Scout copy "No candidates ledgered." — this section's own vocabulary is folds/
  sequences, never candidates.
- **Walk-Forward**'s sequence-verdict block's outer element changed from `<p>` to `<div>` — the
  `<details>`/`<pre>` pair it wraps are block-level elements, illegal inside a `<p>` (React reports
  a hydration error the instant that block is expanded; this showed as a "5 Issues" dev-overlay
  badge). Same classes, same text, same `<details>` content — only the wrapper tag changed.
- **Validation Vault**'s two early-return branches (loading, unreachable/error) now wrap their
  content in `data-testid="validation-vault-section"`, matching the success path (which already had
  it) and matching how `ScoutLedgerSection`/`WalkForwardSection` already keep their own outer testid
  present across every state.

## New user-facing capability

None new on screen — this iteration makes four already-shipped panels fully honest (no
silently-withheld disclosure numbers, no markup defect, no copy-vocabulary mismatch, no missing
testid in a degraded state). Separately (not a UI change), the product's machine surface grows from
22 to 26 read-only MCP tools — see the dev handoff for that half.

## New information displayed

Microscope Readiness: the sealed-tranche aggregate (shard count / symbol-days / per-universe
breakdown) and the joinable-corpus withheld-excluded count — both already served, previously dropped
by the frontend type. Scout Ledger: each family's `family_root_id`.

## New user actions

None — no new button/control. Validation Vault stays read-only.

## UI surface changes

Microscope Readiness gains one small new block (no new top-level section) inside its existing
layout. Scout Ledger's family header gains one field. Walk-Forward's empty-state copy changes and
its sequence-verdict block changes HTML tag (no visible layout change — `<div>` and `<p>` render
identically here; only the DOM node type differs). Validation Vault's loading/unavailable states
gain a wrapper testid (no visible change). No new page, section, or nav entry (`app/meta.py`
`UI_ROUTES` untouched).

## Design system conformance

Reused the existing `MicroReadinessSection`/`ScoutLedgerSection`/`WalkForwardSection`/
`ValidationVaultSection` inline components — no new component file, no new component-library
primitive. The new Sealed Tranche block reuses the SAME plain `<table>`/`EmptyState` markup pattern
every other block in this section already uses; house style stays dark-only/dense/no-glow, no color
implies advice. `withheld_excluded` and the per-universe counts render as plain labeled counts in
the same visual unit as every other diagnostic-class number on this page (Design Direction rule).

## Browser verification performed

Store-scoped rig (`scripts/dev.sh`, backend `:8301` / frontend `:3301`), against Chrome attached at
`127.0.0.1:9222` (this session's carried context — attached rather than self-launched). Console
logging enabled; console messages re-checked after every section expansion and after the one
`<details>` interaction (the exact class of check this round's independent-auditor mandate names).

- **Microscope Readiness**, expanded: zero console errors. New Sealed Tranche block confirmed live
  against the real `.data` store's genuinely all-zero state — `shard_count`/`symbol_days`/
  `withheld_excluded` all render `0` (an honest zero, not blank/missing), and the per-universe table
  correctly falls back to "No sealed shards recorded." Confirmed via raw HTML inspection of each
  `data-testid` value, not merely "the section rendered something."
- **Scout Ledger**, expanded: zero console errors. Real store's Scout ledger is genuinely empty
  ("No candidates ledgered."), so the new `family_root_id` text was NOT visually observed live this
  pass (there is no real family to render it against) — see the dev handoff's Known Issues.
  Type-checked clean (`tsc --noEmit`) against `family.family_root_id: string`.
- **Walk-Forward**, expanded: zero console errors, against a REAL, non-trivial sequence already on
  disk (`seq-d39d20e47af24671`, the era's own 155-session diagnostic run) — not an empty stub.
  Clicked the sequence's own "detail" `<details>` toggle (the exact TC-7 interaction: expand the
  block that previously triggered the hydration error) and re-checked console: **zero new
  messages**. This is a live, execution-based proof of the HTML-nesting fix, not a static scan
  alone (a static whole-file regex scan was ALSO run and independently confirms this was the only
  site in the page with this defect pattern).
- **Validation Vault**, expanded: zero console errors. Directly observed
  `data-testid="validation-vault-section"` present in BOTH the loading snapshot (captured
  mid-fetch, wrapping `validation-vault-loading`) and the settled state (wrapping the full,
  honestly-empty "No shards recorded."/"No universes registered." content) — live proof of TC-10 in
  both states.
- Full-file regex scan confirms zero remaining `<p>` elements anywhere in `page.tsx` containing a
  `<details`, `<pre`, `<table`, or `<div` descendant (the HTML-nesting fix's own completeness
  check).
- `tsc --noEmit` (apps/frontend): 0 errors, including every `MicroReadinessResponse` construction
  and read site.

**Not exercised live this pass** (see dev handoff's Known Issues for the full reasoning): the
NON-ZERO `sealed_tranche`/`by_universe` rendering path and a `family_root_id` genuinely differing
from `family_id`, since the real `.data` store's current state is honestly all-zero/empty for both.
Recommend the QA/browser-qa lane exercise both against a seeded fixture-scoped rig, per the phase
spec's own explicit TC-5 instruction.

## Known Issues

See the dev handoff (`docs/handoffs/goal-rapid-microscope-iter-15-dev.md`) for the full list — in
summary: the non-zero-fixture rendering paths for TC-5/TC-8 and the full J-01–J-05/J-10 regression
sweep (TC-13) are QA/browser-qa-lane work, not reproduced in this dev pass; no "Run Screen"/"Run
Walk-Forward" button was ever clicked (the era's own performance trap).
