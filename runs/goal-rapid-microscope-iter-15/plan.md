# goal-rapid-microscope-iter-15 Execution Plan

Alignment check: on-goal, no drift. This is J-08's second half (evaluator-mandated split from
iteration 14's ESCALATE verdict, full depth per the era's own iter-8/iter-12 precedent — the
auditor lane must not be trimmed this round). Five pieces, all inside J-08/J-07's already-shipped
homes: (a) four MCP proxies + `EXPECTED_TOOLS` 22→26, (b) the Microscope Readiness coherence fix
(`sealed_tranche` + `joinable_corpus.withheld_excluded`, both already served, both aggregate-only),
(c) the Walk-Forward HTML-nesting fix, (d) three minor confirmed defects (`family_root_id`,
Walk-Forward empty copy, Vault testid), (e) genuine J-07 re-verification. Everything the phase spec
marks OUT OF SCOPE (J-06 steps 4-5, J-09, the unrendered `joinable_corpus` sub-fields, a Graduation
UI section, J-10's remaining trap items, spec changes) stays out — no incidental extra scope, so
the budget trimmer has no excuse to drop the auditor step.

## What to Build

- **Four MCP proxy tools** (`apps/backend/app/mcp/__init__.py`) — `desk_micro_readiness` →
  `/research/desk/micro/readiness`, `desk_scout` → `/research/desk/micro/scout`,
  `desk_walkforward` → `/research/desk/micro/walkforward`, `desk_vault` →
  `/research/desk/micro/vault`. Add four `_STATIC_PATHS` entries (after the `desk_referee_registry`
  entry, :140) and four `types.Tool` entries (after the `desk_referee_registry` Tool block, :409,
  before `pnl_ledger`, :410) — copy the `desk_referee`/`desk_referee_registry` no-required-param
  shape exactly (`inputSchema=_object_schema({})`). Update the module docstring's shipped-endpoint
  list (:17-23) in the same commit. No new HTTP verb, no new dependency, no `_request_path` change.
- **`EXPECTED_TOOLS` 22→26** (`apps/backend/tests/test_mcp_server.py`, :60-83) — insert the four
  names immediately after `"desk_referee_registry"` (:78) and before `"pnl_ledger"` (:79), in the
  SAME commit as the tool additions. Add honest-empty-state AND directly-seeded-populated-state
  byte-identity tests per tool (mirror the `desk_referee`/`desk_referee_registry` precedent) —
  seed via each ledger's own public append/record function, NEVER by triggering a live
  screen/fold-run compute (a real Scout run has been observed running past 25 minutes against the
  real corpus with zero completed candidates — no acceptance criterion may depend on one finishing).
- **The MCP-surface TR-2 sweep (new test)** — reuse, don't reimplement, `test_vault.py`'s rig
  (`_combined_fixture_store` :555, `_record_distinctive_dataset` :563, `_scope_everything_to` :605,
  `_scalars` :626). Call all 26 tools via `call_tool` against a backend with one sealed,
  globally-distinctive shard; assert the sealed shard's raw dataset id, checksum, symbol, window
  bounds, and exact trade/quote counts appear in ZERO tool response bodies. The MCP server is a
  genuinely separate process (`python -m app.mcp` over stdio) the existing REST-only
  `app.openapi()`-driven TR-2 sweep never exercises — this closes that gap for the new surface.
  This is the round's opaque-pool-critical item: **byte-identity to the already-audited REST route
  is the acceptance bar for all four tools — a proxy that reshapes, enriches, or joins is not
  compliant, only a verbatim pass-through is.**
- **Microscope Readiness coherence fix** — `apps/frontend/lib/types.ts` `MicroReadinessResponse`
  (:2514-2519) gains `joinable_corpus` and `sealed_tranche` (exact shape below); `page.tsx`'s
  `MicroReadinessSection` (function starts :5886) renders `sealed_tranche.shard_count` /
  `.symbol_days` as two new rows plus a small per-universe (`by_universe`) breakdown, and
  `joinable_corpus.withheld_excluded` as one more labeled count, inside the existing Corpus Totals
  area. AGGREGATE ONLY — no symbol, session date, dataset id, checksum, or per-shard
  `exposure_state` for a withheld shard anywhere in the new markup (this is the SAME opaque-pool
  fault class as the MCP item above, just through the UI transport instead of MCP — both widen the
  identical backend response, so review/audit should confirm both stay narrow, not just one, per
  the twin-check lesson). `joinable_corpus.total`/`playbook_signal_count`/`band_touch_count`/
  `by_setup_id` stay typed/fetched but UNRENDERED this iteration. Zero change to
  `micro_readiness.py` — every field surfaced here is already served by unchanged code.
- **Walk-Forward HTML-nesting fix** (`page.tsx:6461-6472`) — the sequence verdict block wraps a
  `<details>/<pre>` block-level pair inside a `<p>` (verified: React/Next.js reports a hydration
  error here — a "5 Issues" dev-overlay badge appears the instant this block is expanded, lesson
  iter-14: console errors only surface after expansion, not on first load). Change the outer `<p>`
  to a `<div>`, preserving classes/text/`<details>` content exactly. Confirmed by whole-file scan
  to be the ONLY such site in the page — no sibling fix needed.
- **Three minor fixes**: Scout family header (`page.tsx:6198-6203`) — render `family.family_root_id`
  beside `family.family_id`/`variants_tried` (field already on `ScoutFamily`, already fetched, no
  new fetch/type). Walk-Forward empty state (`page.tsx:6444`) — change the reused Scout copy "No
  candidates ledgered." to sequence-appropriate wording (e.g. "No walk-forward sequences run.").
  Validation Vault (`page.tsx:6603-6621`) — its two early returns (:6608-6610 loading,
  :6611-6617 unavailable) skip the `data-testid="validation-vault-section"` wrapper that only the
  success path (:6621) has; wrap all three branches the way `ScoutLedgerSection`/`WalkForwardSection`
  already do (their outer `data-testid` div wraps the loading/unavailable ternary as a child,
  confirmed by reading both — :6123 `scout-ledger-section` wraps unconditionally).
- **Genuine J-07 re-verification** — re-run `tests/test_micro_graduation.py` fresh this iteration
  (not cited from a prior round); browser-qa navigates DIRECTLY to
  `http://<backend-host>:<port>/research/desk/micro/graduation` on the store-scoped rig's backend
  port and captures a screenshot of the HTTP 200 body showing the stage vocabulary. This route has
  no golden replay script BY DESIGN (documented in the route's own docstring, `micro_routes.py`
  :578-589 — `demo_runner.normalize_url()` forcibly rewrites any localhost URL onto the frontend
  base, so a backend-origin navigation cannot be expressed in the replay schema; disclosed at
  `runs/goal-session-rapid-microscope/state/golden-gaps`, not silently missing) — this is the
  correct, permanent verification path, not a workaround. Record this as a real re-verification,
  not a third `DEFERRED-BUDGET`.
- **`_PRICE_ARITHMETIC_FIELDS` extension** (`apps/backend/tests/test_desk_ui_guards.py`, list
  starts :215) — add the newly-rendered numerics: `sealed_tranche.shard_count`/`symbol_days`/its
  `by_universe` counts, `joinable_corpus.withheld_excluded`. Allow-list widening only, never a
  narrowing.
- **Required-still-passing regression**: J-01, J-02, J-03, J-04, J-05, J-10 (J-06 intentionally
  excluded — unchanged from iteration 14's identical precedent). Every cited evidence path must
  exist on disk, not merely be cited (lesson iter-13).

**`MicroReadinessResponse` new fields, transcribed verbatim from `micro_readiness.py`'s
`build_readiness` (:463-495) — add nothing else, drop nothing:**
```ts
joinable_corpus: {
  total: number;
  playbook_signal_count: number;
  band_touch_count: { status: string; count: number | null };
  by_setup_id: Record<string, number>;
  playbook_integrity_errors: { file: string; error: string }[];
  withheld_excluded: number;
};
sealed_tranche: {
  shard_count: number;
  symbol_days: number;
  by_universe: Record<string, { shard_count: number; symbol_days: number }>;
};
```

## Agents Required

- developer: yes — one pass covers the MCP tools, the `EXPECTED_TOOLS`/byte-identity/TR-2-sweep
  tests, the readiness type+render fix, the HTML-nesting fix, the three minor fixes, and the guard
  extension, TDD (tests first per TC).
- backend-data: yes — `apps/backend/app/mcp/__init__.py` (4 new proxies), `test_mcp_server.py`
  (26-tuple + byte-identity tests), the new MCP-surface TR-2 sweep test, `test_desk_ui_guards.py`
  extension. Zero change to `micro_readiness.py`/`vault.py`/`scout.py`/`scout_ledger.py`/
  `walkforward.py`/`walkforward_ledger.py`/`micro_routes.py`'s computation, serialization, or route
  shape — this iteration only adds readers.
- frontend-ux: yes — `lib/types.ts` (2 new fields on `MicroReadinessResponse`), `page.tsx`
  (Microscope Readiness render, Walk-Forward tag fix + empty copy, Scout family_root_id, Vault
  testid wrapper).

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/mcp/__init__.py` — 4 `_STATIC_PATHS` entries + 4 `types.Tool` entries after
  `desk_referee_registry`/before `pnl_ledger`; docstring shipped-list update.
- `apps/backend/tests/test_mcp_server.py` — `EXPECTED_TOOLS` 22→26 (:60-83); empty+populated
  byte-identity tests for the 4 new tools; the MCP-surface TR-2 inference sweep.
- `apps/backend/tests/test_desk_ui_guards.py` — `_PRICE_ARITHMETIC_FIELDS` widened (:215).
- `apps/frontend/lib/types.ts` — `MicroReadinessResponse` (:2514-2519) gains `joinable_corpus` +
  `sealed_tranche` (shape above).
- `apps/frontend/app/desk/page.tsx` — `MicroReadinessSection` (:5886+) renders the two new
  aggregates; `<p>`→`<div>` fix at :6461-6472; `family_root_id` at :6198-6203; empty-state copy at
  :6444; `validation-vault-section` testid wrapper on the two early returns at :6608-6617.
- `docs/handoffs/goal-rapid-microscope-iter-15-dev.md` — new dev handoff (required, TC-16).
- `runs/goal-session-rapid-microscope/state/blueprint.md` — documentation-only note: no new Data
  Contract row (both readiness sub-fields already registered iter-10; the 4 MCP tools are
  transport-layer proxies of already-registered endpoints, per this codebase's own convention that
  no prior MCP proxy ever got its own Data Contract row either).

No change to `micro_readiness.py`, `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
`walkforward_ledger.py`, `micro_routes.py`, any `referee_*.py`, `micro_chain_ledger.py`,
`micro_observer.py`, `micro_features.py`, `micro_graduation.py`, Playbook detectors, `Config`, or
`docs/rapid-validation-spec.md`.

## UI Evolution

- New user-facing capability: none new on screen (the four already-shipped Rapid-Microscope panels
  become fully honest — no silently-withheld disclosure numbers, no markup defect); the product's
  machine surface (Claude + MCP) grows 22→26 read-only tools, making readiness/scout/walk-forward/
  vault bodies newly readable from a conversation.
- New information displayed: Microscope Readiness gains the sealed-tranche aggregate
  (`shard_count`/`symbol_days`/per-universe breakdown) and `withheld_excluded`, both already served,
  previously dropped by the frontend type; Scout Ledger gains `family_root_id` per family.
- New user actions: none — all four new MCP tools are read-only proxies; no new button/control;
  Validation Vault stays read-only.
- UI surface changes: Microscope Readiness gains two small aggregate additions (no new section);
  Scout Ledger's family header gains one field; Walk-Forward's empty copy changes and its
  sequence-verdict block changes tag (no visible layout change); Vault's loading/unavailable states
  gain a wrapper testid (no visible change). No new page, section, or nav entry.
- Navigation changes: none — `app/meta.py` `UI_ROUTES` untouched.

## Visual Requirements

- Component patterns: extend the existing `MicroReadinessSection`/`ScoutLedgerSection`/
  `WalkForwardSection`/`ValidationVaultSection` inline components in `page.tsx` — no new component
  file, no new component-library primitive. Reuse `EmptyState`/`LoadingPanel`/`UnavailablePanel` as
  already wired.
- Layout: continues the single-column, dense, terminal-grade `/desk` layout; the two new readiness
  rows sit inside the existing Corpus Totals block, not a new sub-section.
- Key visual effects: none new — house style stays dark-only/dense/no-glow; no color implies advice
  (Design Direction). The `by_universe` breakdown is small plain text/rows, not a chart.
  `withheld_excluded` renders as a plain labeled count beside the existing totals, in the same
  visual unit as other diagnostic-class numbers per the Design Direction rule.
- States to handle: TC-5 must be exercised against BOTH the real `.data` store's current
  all-zero `sealed_tranche`/`withheld_excluded` state (honest zero, not blank) AND a non-zero
  fixture state (so the rendering path is proven, not merely inert) — Validation Vault's
  loading/unavailable/populated states are unchanged this iteration except for the testid wrapper.

## Key Test Scenarios

(Condensed from the phase spec's TC-1…TC-16 — see
`docs/phases/goal-rapid-microscope-iter-15.md` for full text.)

- TC-1/TC-2/TC-3: `EXPECTED_TOOLS` and `list_tools()` both equal the 26-entry ordered tuple; each
  of the 4 new tools is byte-identical to its own GET route on both honest-empty and a
  directly-seeded populated state (never via a live compute run).
- TC-4 (auditor-critical): all 26 tools swept against a fixture with one sealed, distinctive
  shard whose original pool is not yet fully released — its raw dataset id, checksum, symbol,
  window bounds, and trade/quote counts appear in ZERO tool response bodies.
- TC-5/TC-6: a fixture readiness store with non-zero `sealed_tranche`/`withheld_excluded` renders
  those exact numbers on screen, byte-matching the fetched JSON (compare on-screen value to the
  underlying response, not merely "present" — lesson iter-14); the rendered DOM contains no
  symbol/date/dataset id/checksum/per-shard row for any withheld shard.
- TC-7: expanding a Walk-Forward sequence's detail produces zero new console/dev-overlay errors
  and the rendered block passes HTML validation (no block-level element inside `<p>`).
- TC-8/TC-9/TC-10: Scout family header shows both `family_id` and `family_root_id`; Walk-Forward's
  empty state title is not "No candidates ledgered."; Vault's `validation-vault-section` testid is
  present in loading AND unavailable/error branches.
- TC-11: `test_micro_graduation.py` re-run fresh, all cases pass; browser-qa captures a screenshot
  of `GET /research/desk/micro/graduation` (HTTP 200, stage vocabulary visible) via direct
  backend-port navigation on the store-scoped rig — this iteration's genuine J-07 re-verification.
- TC-12: widened `_PRICE_ARITHMETIC_FIELDS` sweep reports zero client-side arithmetic on any
  newly-rendered numeric.
- TC-13: J-01–J-05 and J-10's replay/browser-QA evidence files genuinely exist on disk at their
  cited paths.
- TC-14: full suite ≥ 3228 collected / 0 failed; fingerprint `08e471b10130e1e2`; all six
  `referee_*.py` + `micro_chain_ledger.py` SHA-256 hashes unchanged from era-open baseline; zero
  new `Config` fields; Playbook detectors byte-untouched.
- TC-15: clean `rm -rf apps/frontend/.next` + rebuild (T-9); `tsc --noEmit` exits 0 including every
  `MicroReadinessResponse` call site.
- TC-16: `docs/handoffs/goal-rapid-microscope-iter-15-dev.md` AND an independent audit report both
  exist on disk for this iteration — not silently substituted with a lean/trimmed run.

**Performance trap (do not violate):** a live Scout compute against the real corpus has run past
25 minutes without producing one completed candidate. No acceptance criterion in this iteration may
depend on a completed Scout (or Walk-Forward) run finishing — all populated-state tests seed
directly via ledger/store write functions, never by clicking "Run Screen"/"Run Walk-Forward" and
waiting.

**Auditor mandate (why this round must not lose the auditor lane):** re-sweep the four new MCP
tools AND the widened Microscope Readiness panel specifically against the TR-2 inference-trap
methodology — confirm neither surface discloses more than its already-audited REST endpoint does.
This exact fault class has been caught by the independent auditor alone six times this session
(rounds 2, 4, 5, 7, 13, 14), always after review and QA had already passed the same code. Attack
the fix before it's written up, not after.
