# Goal Iteration 33 — J-12: Feature Snapshots gets a surface (desk section + MCP v8); the enumerator's two silent exclusions become honest counts

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 33
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-12
- **Required-still-passing journeys:** J-01, J-02, J-04, J-08, J-10, J-11 (J-01 is the
  dependency-order sibling immediately above snapshots in "readiness → snapshots → scout"; J-02
  is the journey whose golden this iteration extends and whose owed element close-up rides this
  round; J-04 is the next sibling below snapshots in that same dependency order; J-08 owns the
  MCP tool-count contract this iteration bumps v7→v8 and the shared `/desk` surface; J-10 is the
  full-product sentinel; J-11 owns the immediately-adjacent Graduation section this iteration's
  new section renders directly below. J-03/J-05/J-06/J-07/J-09 are excluded: no `/desk` section
  of their own or unaffected by this iteration's surface — their stored goldens are untouched and
  keep replaying on their own schedule.)
- **Anti-goal reminders:**
  - *Immutable rails (critical; "only ever grow more specific, never weaker"):*
    1. No execution path, ever — no brokerage/trading API, no order tickets, no live OR paper
       trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py`
       is the tier-1 guard; new research code adds matching guard tests, never weakens them.)
    2. No profit claims and no advice — every $ figure is a simulated measurement carrying R,
       n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction
       language, no imperative trading cues.
    3. Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five
       states and thresholds, the frozen structure computations, the JSON `BarStore`, and
       every KEPT surface's behaviour stay byte-identical. New work is additive and versioned
       beside them, never a mutation of them.
    4. Hold-out-only promotion — the champion pointer moves only on a genuine hold-out
       survival through the sweep gate PLUS a valid Referee certificate. Train-only wins are
       labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
       feeds/fingerprints to manufacture a survivor.
    5. No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    6. Single source of truth — each shared value is computed once, owned by one canonical
       endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor
       hard-fails violations.
    7. Deterministic and seeded — every random draw uses a recorded named seed via per-row
       streams; identical requests reproduce byte-identical results; no wall-clock, no
       unseeded randomness in any research artifact.
    8. Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on
       the MCP surface can change state.
    9. Immutable data — registered datasets and bar series are append-only, checksummed,
       never re-tagged, never deleted, never content-perturbed. Splits are frozen at
       registration.
    10. Persistence stays scoped — no ambient recording of live streams; recording/fetching
        is an explicit, logged act.
  - *Era-B/B2 anti-goals (still binding):* membership is never a signal; snapshots and
    playbook records are append-only and pinned; every run is an explicit operator act; the
    briefing and the playbook describe, never advise; the demolition stays demolished; the
    ledger never holds orders; the suite stays keyless and hermetic; the fingerprint pin does
    not move; no threshold exists outside its spec and no code path sweeps one; the evidence
    pools one signature; no recorded playbook file is ever rewritten; no second implementation
    of the measurement rail.
  - *Referee-era anti-goals (still binding):* no confirmatory claim outside the gauntlet; the
    historical atlas is exploratory forever; CI-inversion is never a p-value; never shrink the
    BH denominator; no gate loosens mid-era; the Referee never feeds back; promotion is
    certificate-locked with no bypass; no confirmatory output without a verified oracle
    attestation; no annualized metrics anywhere.
  - *Rapid-Microscope anti-goals (added, not weakening any rail above):*
    - No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed`
      shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
      exposure; the refusal is typed, tested, and fail-closed.
    - Sealed exposure is family-level and single-shot — never a second draw. No more than one
      evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
      travels in every later export bundle; no perturbed re-submission resets it.
    - A recorded tranche is one opaque research pool until its shards are exposed. No served
      surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout,
      walk-forward, graduation, MCP, UI — may present a complete identity-labelled partition
      of "exploratory" versus "sealed", nor a complete per-shard list of EITHER side while any
      pool member is unexposed. The governing test is the TR-2 inference trap: given the
      registered universe plus every public artifact, no still-unexposed vault-eligible shard
      is identifiable with certainty. This spec's `withheld_excluded` addition MUST be a
      pool-derived count, never a snapshot-file-derived one (a snapshot file's mere presence
      or absence for a withheld id would leak sealed-pool build state).
    - Evidence classes never mix. No `historical_exposed_diagnostic` output feeds a gate, a
      graduation transition, a certificate, a promotion, or a pooled statistic with
      `historical_oos` rows; nothing in this era emits `live_confirmatory`.
    - No fold geometry change after fold 1 without a recorded voiding event that clears every
      survivor state of that corpus-era.
    - No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
      validation, sealed, or holdout outcomes. Fitting rules are data functionals frozen
      before reveal; per-origin refits under an unchanged rule are provenance, never a new
      choice.
    - The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger
      with a closed-vocabulary decision; kills are never deleted; the union-N across grid
      versions is served beside every family.
    - The accessor is the only data door. No module but `micro_accessor.py` opens snapshot or
      vault event data; origin fences fail closed; import-ban and source-scan guards enforce
      it.
    - No microstructure claim beyond what L1 supports. `refill_consistent` is the strongest
      liquidity label; "iceberg", institutional-intent, and manipulation language are banned;
      every aggressor-derived quantity is served beside its `fallback_frac` and
      `unknown_frac`.
    - No sub-second outcome horizon and no latency-sensitive mechanism, per DO-NOT #1.
    - No cross-unit liquidity arithmetic. No feature, screen, or study relates trade shares to
      displayed quote sizes unless the dataset's `quote_size_unit` is verified; unverified or
      mixed units are a typed refusal.
    - No value is served before it exists. Every feature carries
      `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable`
      until its observations exist; no outcome for a conditioned anchor begins before the
      conditioning set's maximum `available_at` (TR-17).
    - The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never
      `historical_oos`, never relabeled.
    - The ~150-symbol-day research-readiness gate is never lowered or silently satisfied; any
      claim whose predeclared floor is unmet fails closed with the floor arithmetic served.
    - Referee modules are byte-untouched this era — `referee_handoff_ready` never implies
      current-Referee registrability of a flow predicate; that awaits a future named revision
      of the referee spec.
    - The vault secret never enters the repo, a log, a payload, or a screenshot — only its
      sha256 commitment is ever recorded.
    - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY
      inside the `AUTO:journeys` marker block of `docs/goal.md` — it MUST NOT edit
      human-authored journeys, the Anti-goals section, or any other part of that file;
      proposed journeys MUST carry a single-source-of-truth acceptance criterion, keep the
      `default` profile and `v1` byte-identical, respect every rail above, and include a
      `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop
      alive is a failure.
  - *Host protection (carried verbatim — a physical constraint of the host, not product
    scope):* Host-guard caps are law. When `project-extensions/host-guard/host-guard.env`
    declares ceilings (CPU mask `4-7,12-15` plus BLAS thread caps and memory/task bounds),
    every heavy path respects them; the engine pauses `AWAITING_HOST_GUARD` (resumable) only
    when confinement cannot be established. Never disable, widen, or bypass these caps to make
    a run faster or a pause go away.

## GOAL

Ship J-12: a read-only **Feature Snapshots** section on `/desk` (directly below the shipped
Graduation section) that renders `micro_snapshots.py`'s already-computed inventory verbatim, plus
two new honest disclosure counts (`withheld_excluded`, `stale_excluded`) on the SAME
`GET /research/desk/micro/snapshots` route so an operator can finally tell "never built" from
"built, then invalidated" instead of seeing a bare `[]`, plus a byte-identical `desk_micro_snapshots`
MCP proxy (contract v7→v8, 27→28 tools) and J-02's owed golden extension + element close-up.

## BACKGROUND

Iteration 32 ended GOAL_ACHIEVED with all eleven journeys green and the evaluator's recommended
next step for iteration 33 was `evidence`-depth tidying (J-11's walkthrough, J-02/J-03 close-ups,
J-05's golden wording) — three items with **no code change**. Between that eval and this dispatch,
the goal-proposer appended **J-12** inside `docs/goal.md`'s `AUTO:journeys` marker block —
currently an UNCOMMITTED working-tree change (`git status --porcelain -- docs/goal.md` shows
` M docs/goal.md`, 84 lines added; confirmed by reading the diff directly), the only mechanism by
which new scope may legally enter this era. J-12 is genuinely new: it is absent from
`journey-history.json`'s 11-journey ledger (`grep -c "J-12" journey-history.json` = 0), never
attempted. I independently re-verified its premise against the tree rather than trusting the goal
text: `GET /research/desk/micro/snapshots` (`micro_routes.py:167-177`) serves only
`{"snapshots": list_snapshot_meta(...)}` with no disclosure counts at all today;
`list_snapshot_meta` (`micro_snapshots.py:363-386`) silently `continue`s past withheld ids with no
count kept, and silently drops a stale meta (`load_snapshot_meta` returning `None` on an identity
mismatch, `micro_snapshots.py:333-360`) with no count kept either — so the listing can serve `[]`
with 18 real meta files on disk and give the operator zero explanation. `micro_snapshots.py` has
zero UI readers and no named MCP tool (`grep -rn micro_snapshots apps/frontend/` and
`test_mcp_server.py`'s 27-tuple both confirmed empty of it) despite being an already-registered
Data Contract row since era baseline.

**This overrides the dispatch line's `evidence` depth recommendation.** That recommendation was
iter-32's own next-step call, computed before J-12 existed and while literally every Target
journey was already `passing` — rule 7 forbids planning an evidence-only iteration once real,
machine-buildable work exists, and J-12 (new backend fields + new frontend section + new MCP tool)
is exactly that. This is the identical situation iter-31 faced for J-11's appearance, and this
spec follows that iteration's own resolution.

**Depth: lean, not full.** J-12 is full-stack (backend route additions + guard-test extensions,
frontend `/desk` section, MCP proxy) but none of the four full-depth escape conditions holds:
prior verdict was GOAL_ACHIEVED (not ESCALATE/REGRESSION); iter-32 has no `coherence.md` FAIL on
record; consecutive lean count is 3 of a cadence-6 threshold (not due); and trigger 4 ("brand-new
full-stack journey ... with real Data-contract additions") does not fire because J-12's own
Acceptance text explicitly disclaims one: "no second computation path, no new endpoint, no Data
Contract row added, existing keys byte-identical with only `withheld_excluded` and
`stale_excluded` added". This is the depth rubric's own named lean example — "a new endpoint plus
its UI use" — here, additive fields on an already-registered endpoint plus new UI/MCP readers of
it. Trigger 2 (data-model migration) also does not fire: this is purely additive work (two new
response fields), explicitly carved out by the trigger's own text. This deviation (from `evidence`,
not to `full`) is logged to the assumption ledger.

**Anchors verified in the tree today** (re-locate by symbol name, not line arithmetic — these may
drift): `GET /snapshots` route at `apps/backend/app/research/micro_routes.py:167-177`;
`list_snapshot_meta`/`load_snapshot_meta`/`withheld_dataset_ids_for_store`/`exclude_withheld` at
`apps/backend/app/research/micro_snapshots.py:148-386`; the compute-progress route already has a
`withheld_excluded` field in its OWN payload shape (`micro_snapshots.py:489,536,554,609`) that this
iteration's listing-route field must match in meaning (a pool-derived count) but is a SEPARATE
field on a separate route, never shared code beyond the one shared predicate; the MCP static-path
table and `types.Tool` list live in `apps/backend/app/mcp/__init__.py`
(`_STATIC_PATHS["desk_micro_readiness"]` at line 149, its `types.Tool` entry at lines 428-442 —
`desk_micro_snapshots` is the next sibling per the dependency-order rule, positioned between
`desk_micro_readiness` and `desk_scout`); `EXPECTED_TOOLS` (27-tuple today, confirmed by direct
read) and the write-verb/arg-shape guards live in `apps/backend/tests/test_mcp_server.py`;
`_PRICE_ARITHMETIC_FIELDS` lives in `apps/backend/tests/test_desk_ui_guards.py`; the Graduation
section (`GraduationSection`, its `<section aria-label="Graduation">` wrapper, and the
`CollapsibleSection id="graduation"` pattern) is the last Rapid-Microscope section in
`apps/frontend/app/desk/page.tsx`, immediately before `</main>` — Feature Snapshots is the next
sibling, immediately below it (T-11); J-02's stored golden lives at
`runs/goal-session-rapid-microscope/journey-scripts/J-02.json` and today asserts only the
pre-existing "Fallback frac" string (per iter-19's note), sharing that string's SECTION with no
other journey but carrying no snapshot-specific assertion of its own.

**Lessons applied:** T-9 (clean rebuild before browser evidence), T-10 (evidence honesty — no
screenshot ⇒ `unknown`; element-capture for the new section, and the era-6 lesson that a
full-page `/desk` capture is not trustworthy — crop an element instead), and T-11 (the new section
renders below shipped ones, reuses no shipped `data-testid`/heading string, is statically swept
against stored replay scripts) all govern this iteration directly. Iter-31's second lesson (run
the T-11 sweep against the stored scripts' EXPECT TEXTS, not just testids/headings) applies
directly to J-02's golden extension below. Iter-30's lesson (a below-the-fold screenshot can be
byte-identical to an unrelated journey's shot unless it targets the SSR'd element specifically)
governs the J-02 close-up capture. Iter-25's "re-check the GROUNDS of a carried-forward premise"
governed this spec's own independent re-derivation of J-12's premise above rather than trusting
the goal text.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/micro_snapshots.py`: `list_snapshot_meta` (or a thin wrapper
      called by the route) additionally returns `withheld_excluded` (count of ids `exclude_withheld`
      dropped from the pool — the SAME choke point every other corpus-wide enumerator already
      shares, matching the `GET /research/datasets` `sealed_withheld` and
      `GET .../snapshots/compute` `withheld_excluded` disclosure convention) and `stale_excluded`
      (count of meta files present on disk whose `load_snapshot_meta` identity re-verification
      failed — computed AFTER the withheld filter, never counting a withheld id twice, and never
      carrying the stale VALUE itself, only its count).
- [ ] `apps/backend/app/research/micro_routes.py`: `get_micro_snapshots` (`GET /snapshots`) response
      grows to `{"snapshots": [...], "withheld_excluded": int, "stale_excluded": int}` — existing
      `snapshots` key byte-identical, no new endpoint, no second computation path.
- [ ] `apps/backend/app/mcp/__init__.py`: add `desk_micro_snapshots` to `_STATIC_PATHS` (value
      `/research/desk/micro/snapshots`) and its `types.Tool` entry, positioned immediately after
      `desk_micro_readiness` and before `desk_scout` (dependency-order sibling rule), matching the
      existing `desk_micro_readiness`/`desk_scout` no-required-param, byte-identical-GET-proxy shape
      exactly.
- [ ] `apps/backend/tests/test_mcp_server.py`: extend `EXPECTED_TOOLS` to the 28-tuple with
      `desk_micro_snapshots` immediately after `desk_micro_readiness` (guard tests are extended,
      never edited).
- [ ] `apps/backend/tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` with every
      served snapshot numeric the new section renders (`row_count`, `bytes_on_disk`,
      `withheld_excluded`, `stale_excluded`), plus a seeded counter-test proving the guard is live.
- [ ] `apps/backend/tests/test_vault.py`: confirm/extend the TR-2 join-resistance sweep and the
      MCP-surface-closure structural test cover `/research/desk/micro/snapshots` now that it has
      new disclosure fields and an MCP proxy; add/extend a counter-test proving `withheld_excluded`
      is pool-derived (via `withheld_dataset_ids_for_store`) rather than snapshot-file-derived.
- [ ] `apps/backend/tests/test_micro_snapshots.py` and/or `apps/backend/tests/test_micro_routes.py`:
      new unit coverage for `withheld_excluded`/`stale_excluded` against a fixture with a valid
      snapshot, a stale meta, and a withheld pool member (see fixture-scoped browser TC below).

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: add a `FeatureSnapshotsSection` component + its
      `<section aria-label="Feature Snapshots">`/`<CollapsibleSection id="featureSnapshots">`
      wrapper, rendered as the next sibling directly below the Graduation `<section>`, fetched
      lazily on expand from `GET /research/desk/micro/snapshots` (the same one-fetch-on-toggle
      pattern the other Rapid Microscope sections already use) and rendered verbatim: per
      snapshot its `dataset_id`, `snapshot_format_version`, `micro_algo_version`,
      `config_fingerprint`, `feature_source_hash`, `params_hash`, `quote_size_unit`, `row_count`,
      `bytes_on_disk`, `built_utc`, plus `withheld_excluded` and `stale_excluded` as disclosure
      counts and the build-run history (from `GET .../snapshots/runs`) newest-first — no
      client-side aggregate, derived count, re-ordering, or recomputation of any served value; the
      served empty-state copy renders verbatim when the list or run log is empty. Read-only: no
      build button, no POST — `/snapshots/compute` stays UI-unreachable.

### New user-facing capability
The operator (and Claude via MCP) can now see the Rapid-Microscope funnel's feature-build truth —
which datasets have a currently-valid snapshot, their exact identity fields, and how many pool
members are withheld vs. stale-and-dropped — directly on `/desk`, without reading 18 meta files by
hand or issuing a raw `curl`.

### New information displayed
Per snapshot: `dataset_id`, `snapshot_format_version`, `micro_algo_version`,
`config_fingerprint`, `feature_source_hash`, `params_hash`, `quote_size_unit`, `row_count`,
`bytes_on_disk`, `built_utc` — all already computed and stored by `micro_snapshots.py`, newly
rendered. Two NEW disclosure counts on the same route: `withheld_excluded`, `stale_excluded`. The
build-run history (already served by `GET .../snapshots/runs`), newly rendered.

### New user actions
None (read-only section; no build/compute control — `/snapshots/compute` stays a
manager/CLI-driven, non-UI act per T-8).

### UI surface changes
`/desk` gains one new collapsible section, "Feature Snapshots", rendered directly below the
shipped Graduation section, in the same visual idiom (dark, dense, terminal-grade) as the other
Rapid Microscope sections.

### Product surface delta
The Rapid Microscope's five-section `/desk` block (Readiness, Scout Ledger, Walk-Forward,
Validation Vault, Graduation) becomes six sections with Feature Snapshots appended at the bottom;
the MCP surface grows from 27 to 28 read-only tools; `GET /research/desk/micro/snapshots` gains
two disclosure fields on its existing response shape.

### Blueprint conformance
Lives under the existing Information Architecture home `Desk (/desk) → Rapid Microscope` (see
`runs/goal-session-rapid-microscope/state/blueprint.md`), as the sixth section in that
already-registered group. Purely additive — no nav-skeleton change, no reapproval file needed.
J-02's Information Architecture row is updated in the same edit to point at this new section as
its canonical home (previously a loose "surfaces via Microscope Readiness" reference that this
iteration corrects to the section actually built for it).

### Data-contract additions
None as a new row. The "Feature snapshot metadata + build progress/runs" row (owner
`micro_snapshots.py`, endpoint `GET /research/desk/micro/snapshots`) is already registered in the
blueprint's Data Contract since era baseline and its shape stays unchanged except for two ADDITIVE
fields, both already anticipated by the blueprint's own iter-10 "Disclosure sub-fields" table
(which already names `micro_snapshots.py` as a parent module sharing the `withheld_excluded`
predicate — `withheld_excluded: int >= 0`, pool-derived via the shared
`vault.withheld_dataset_ids()` → `micro_snapshots.exclude_withheld()` choke point). The genuinely
NEW field is `stale_excluded: int >= 0` — a count only, computed post-withheld-filter by
`micro_snapshots.py`, served by the SAME `GET /research/desk/micro/snapshots` route, never a stale
value itself. The blueprint is updated to add `stale_excluded` as a new sub-field row (matching the
file's own iter-10/iter-11/iter-12 precedent for sub-field additions to an already-registered
parent row) and to register the new UI/MCP readers under the existing row, matching the file's own
iter-15/iter-31 precedent for MCP-tool additions.

## OUT OF SCOPE

- Any change to `micro_snapshots.py`'s build logic (`run_snapshot_build_and_record`,
  `build_snapshot_rows`, snapshot identity computation) — this iteration adds disclosure counts
  and readers to the ALREADY-frozen build/listing machinery, never touches how a snapshot is built.
- A build/compute control on the Feature Snapshots section — `/snapshots/compute` stays a
  non-UI, manager/CLI-driven act (T-8).
- Any change to `micro_readiness.py`'s own served payload or the shipped Microscope Readiness
  section — this iteration's new section is a SIBLING, not a replacement or extension of it.
- Any PnL ledger append, strategy/profile/candidate registration, or champion-pointer movement.
- Any `Config` field addition or fingerprint movement.
- J-03's owed element close-up and J-05's golden self-text fix — unrelated to J-12's own surface
  (Structure×Flow and Walk-Forward respectively); not planned this round (rule 5: avoid stacking
  unrelated work onto a single-journey lean spec beyond what naturally rides the same browser
  pass); may ride passenger only if the browser-qa pass below happens to produce them at zero
  marginal cost, never as a goal of this iteration. J-11's owed `[NEW]`-flagged walkthrough step
  likewise stays with the showcase/closing lane, which runs regardless of this iteration's depth.
- Recording more real tape, revealing/assigning any sealed shard, or running the three pilot
  studies against the real recorded corpus (standing out-of-scope, unchanged).
- Re-opening the two owner-deferred anti-goal items (chain-ledger identity r8; sealed-judge econ
  floor r9) or the four `framework_backlog` items — settled, non-blocking, outside this
  iteration's scope; do not re-litigate per iteration-state's "Do not redo" list.

## DEFINITION OF DONE

- [ ] J-12 passes via browser-qa-agent: the Feature Snapshots section renders below Graduation on
      the real store (served list or honest empty state, both disclosure counts, build-run
      history) and, on a fixture-scoped rig seeded with one valid snapshot, one stale meta, and
      one withheld pool member, renders the valid snapshot's every identity field while the stale
      meta appears ONLY inside `stale_excluded` and the withheld member appears ONLY inside
      `withheld_excluded` — each state with its own element screenshot on record.
- [ ] `desk_micro_snapshots` MCP tool ships, byte-identical to its GET route; `EXPECTED_TOOLS` is
      the 28-tuple with `desk_micro_snapshots` immediately after `desk_micro_readiness`; the
      write-verb/arg-shape guards pass unweakened.
- [ ] `_PRICE_ARITHMETIC_FIELDS` covers every served snapshot numeric with a passing seeded
      counter-test; the TR-2 sweep and the MCP-surface-closure structural test pass with
      `/research/desk/micro/snapshots` included; a counter-test proves `withheld_excluded` is
      pool-derived, not snapshot-file-derived.
- [ ] J-02's stored golden replay script gains an additional assertion on a statically rendered
      Feature-Snapshots string unique to it (the SSR'd section shell, never async-loaded row or
      `<option>` text), and that same element capture serves as J-02's owed element close-up
      (clearing its `evidence_makeup` flag).
- [ ] No PnL number moves and none is invented: `GET /research/pnl/ledger` and
      `reports/pnl/pnl-history.md` byte-identical before/after, champion pointer still
      `v1`/`default`, both founding rows still `n = 1 < 5`.
- [ ] Required-still-passing journeys (J-01, J-02, J-04, J-08, J-10, J-11) remain green —
      deterministic replay for every journey with a stored golden.
- [ ] No anti-goal violation introduced; `config_fingerprint` still prints
      `08e471b10130e1e2`; all six `referee_*.py` files still hash byte-identical to the
      iteration-0 listing; every shipped `/`, `/structure`, `/desk` section still renders as
      shipped.
- [ ] Unit tests pass; full backend suite green at a count ≥ the iter-32 baseline (3,503 passed /
      8 skipped) with 0 failures.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-33-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-12 (new — Feature Snapshots section, real-store list-or-empty state + fixture-scoped
  valid/stale/withheld render); J-01, J-02, J-04, J-08, J-10, J-11 (regression, via stored
  goldens).
- Unit/integration: `apps/backend/tests/test_mcp_server.py` (EXPECTED_TOOLS 28-tuple, write-verb
  guard, arg-shape guard); `apps/backend/tests/test_desk_ui_guards.py`
  (`_PRICE_ARITHMETIC_FIELDS` extension + counter-test); `apps/backend/tests/test_vault.py`
  (TR-2 sweep, MCP-surface-closure structural test, pool-derived-not-file-derived counter-test);
  `apps/backend/tests/test_micro_snapshots.py` / `test_micro_routes.py` (new
  `withheld_excluded`/`stale_excluded` unit coverage against a fixture with all three cases).
- Error cases: a malformed/missing snapshots payload must not crash the section (matches the
  existing defensive-read pattern the other Rapid Microscope sections already use); a withheld
  pool member must never surface by id, symbol, session date, checksum, row count, or bytes in
  ANY served field; a stale meta must never surface as a row or carry its stale value anywhere.

Test-first contract:

- TC-1: given the real store's snapshot listing, when the `/desk` Feature Snapshots section is
  expanded, then it renders the served `snapshots` list (or the served empty state) verbatim
  beside `withheld_excluded`, `stale_excluded`, and the build-run history, with an element
  screenshot on record.
- TC-2: given a fixture-scoped rig seeded with one valid snapshot, one stale meta (present on
  disk, identity-mismatched), and one withheld pool member, when the Feature Snapshots section is
  expanded, then the valid snapshot's `dataset_id`/`snapshot_format_version`/`micro_algo_version`/
  `config_fingerprint`/`feature_source_hash`/`params_hash`/`quote_size_unit`/`row_count`/
  `bytes_on_disk`/`built_utc` are all visible, the stale meta appears nowhere as a row and its
  count is reflected only in `stale_excluded`, and the withheld member appears nowhere by id,
  symbol, session date, checksum, row count, or bytes and its count is reflected only in
  `withheld_excluded`.
- TC-3: given the new `desk_micro_snapshots` MCP tool is called, when its response is compared to
  `GET /research/desk/micro/snapshots`'s own response body, then the two are byte-identical.
- TC-4: given `apps/backend/tests/test_mcp_server.py` is run, then `EXPECTED_TOOLS` is a 28-tuple
  with `desk_micro_snapshots` immediately after `desk_micro_readiness`, and the write-verb/arg-shape
  guards pass for the new tool.
- TC-5: given `apps/backend/tests/test_desk_ui_guards.py`'s seeded counter-test for the new
  snapshot numeric fields in `_PRICE_ARITHMETIC_FIELDS`, when a deliberately-violating expression
  is injected, then the guard test fails as expected (proving it is live, not vacuous).
- TC-6: given `apps/backend/tests/test_vault.py`'s TR-2 sweep and the MCP-surface-closure
  structural test, when re-run after `desk_micro_snapshots` is added, then
  `/research/desk/micro/snapshots` is present in `research_tool_paths` and
  `research_tool_paths <= swept` still holds.
- TC-7: given a counter-test that computes `withheld_excluded` from a snapshot-file-count basis
  instead of the pool predicate, when that counter-test runs, then it fails — proving the shipped
  implementation is pool-derived, not snapshot-file-derived.
- TC-8: given J-02's stored golden replay script before this iteration (asserting only "Fallback
  frac"), when this iteration ends, then it additionally asserts a statically rendered
  Feature-Snapshots-section string unique to it, and `demo_runner.py --mode verify` passes it.
- TC-9: given `GET /research/pnl/ledger` and `reports/pnl/pnl-history.md` captured before this
  iteration, when re-checked at the end, then both are byte-identical, the champion pointer is
  still `v1`/`default`, and both founding rows still carry `n = 1 < 5`.
- TC-10: given `Config().config_fingerprint()` and the six `referee_*.py` iteration-0 SHA-256
  listing, when re-checked at the end of this iteration, then the fingerprint prints
  `08e471b10130e1e2` and all six hashes match.
- TC-11: given the full backend suite, when run at the end of this iteration, then it passes at a
  count ≥ 3,503 (the iter-32 baseline) with 0 failures.
- TC-12: given the Required-still-passing journeys' stored goldens (J-01, J-02, J-04, J-08, J-10,
  J-11), when `demo_runner.py --mode verify` runs, then all pass with 0 regressions.

## NOTES

- This spec deliberately deviates from the dispatch line's `evidence` depth recommendation (to
  `lean`, not `full`); see BACKGROUND's dedicated paragraph and the matching assumption-ledger
  entry (`iter-33 — goal-decomposer`) for the full reasoning. This mirrors iter-31's own
  resolution of the identical J-11 situation.
- `docs/goal.md`'s J-12 addition is currently an uncommitted working-tree change. This spec does
  not commit it; that stays whatever process (owner or engine) normally commits goal-text changes
  in this session.
- The three small evidence-only tidy items named by iter-32's evaluator (J-11's walkthrough,
  J-03's close-up, J-05's golden wording) are NOT this iteration's targets; J-02's close-up is the
  one that rides this round because J-12's own step 5 explicitly folds it in. The remaining two
  items stay owed and non-blocking — they belong to a future evidence-only round or the closing
  showcase tail, never manufactured into a round of their own (rule 7).
- The six previously-open, owner-dispositioned anti-goal findings (r8, r9, four
  `framework_backlog` items) are unaffected by this iteration and are NOT re-litigated — per
  iteration-state's "Do not redo" list.
- If the evaluator judges J-12 was not a legitimate proposer addition (e.g., the "manufacturing a
  low-value journey" anti-goal fires), that is a call for the evaluator/owner, not pre-empted
  here — this spec only builds what J-12's own Acceptance text specifies.
