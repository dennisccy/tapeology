# goal-rapid-microscope-iter-7 Execution Plan

Session: `rapid-microscope` · Era: "The Rapid Microscope" · Target journeys: **J-06** (step 1 of 5
only — the Card-5.1 preservation prerequisite), **J-05** (close the last named acceptance gap),
**J-10** (kept-product re-proof). Required-still-passing: J-01, J-02, J-03, J-04. Depth `full`
(mandatory — prior verdict `ESCALATE`, the 4th consecutive full dispatch following an ESCALATE:
iters 4, 5, 6 each returned ESCALATE again).

Canonical sources (read from, never re-derived): phase spec
`docs/phases/goal-rapid-microscope-iter-7.md` (its own DEFINITION OF DONE / TC-1…TC-12 is the
source of truth; this plan condenses it, never replaces it); `docs/rapid-validation-spec.md` §7.1
(preservation prerequisite, lines 405-418) and §2.6 (schema-basis/size-unit contract, lines
154-176); `docs/handoffs/goal-rapid-microscope-iter-6-{dev,audit}.md` (what iter-6 shipped —
TR-15 wiring, tick-corpus exposure seed — and its open findings B1-B5/E1-E4, whose "Recommended
Next Step" this iteration executes almost verbatim); `runs/goal-session-rapid-microscope/state/
iteration-state.md` ("Do not redo" list).

## Alignment check

Directly implements goal.md J-06 step 1 (spec §7.1 r2) and closes the one remaining gap in J-05's
acceptance sentence (iter-6 audit finding B3: "the tick-family fold request returns the typed
floor-refusal naming `11 < 105`" had no production entry point, only a synthetic-date unit test).
Both are named explicitly by the iteration-6 evaluator's own recommended next step and by this
phase spec's BACKGROUND section. No drift found: zero edits to `micro_features.py`/
`micro_observer.py`/`micro_snapshots.py` (iter-3 lesson — touching those forces a whole-corpus
snapshot rebuild for zero benefit; they already implement the `quote_size_unit` contract per J-02);
zero engine change; zero `referee_*` module change; zero new `Config` field; zero fingerprint
movement expected (`08e471b10130e1e2` stays pinned).

Two interpretation calls are already decided by the phase spec's own assumption ledger (iter-7,
both entries) — not open questions for the developer to re-litigate: (1) the §2.6
`schema_basis`/`quote_size_unit` work is storage CAPABILITY only this iteration; the dated vendor
RULE constant (`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`) stays reserved for `tick_recorder.py`'s own
future scope; (2) the tick-family fold request is wired through the CLI only — `POST
/walkforward/compute`'s family parameter is explicitly deferred, since no UI/MCP journey consumes
it yet.

**Frontend Present is declared `yes` even though this iteration's diff is 100% backend/CLI** —
confirmed working precedent from iter-6 (`iteration-state.md`: *"`Frontend Present: yes` WORKED —
keep it"*). See the dedicated section below for the mechanical reason.

## What to Build

### Backend — J-06 step 1: Card-5.1 preservation prerequisite (spec §7.1/§2.6), additive/optional throughout

1. `apps/backend/app/providers/adapters/base.py` — `RawTrade` (`:65`) gains optional
   `conditions: list[str] | None = None`, `exchange: str | None = None`, plus whatever other
   immutable vendor identifiers the spec names by example (`tape`, `trade id`) that the REAL
   Alpaca SDK trade object actually carries — read the live SDK response shape directly, never
   guess a field name. `RawQuote` (`:74`) gains the vendor's quote-condition and bid/ask-exchange
   (venue) equivalents, same optional-default-`None` discipline, only for fields the SDK response
   actually provides.
2. `apps/backend/app/providers/base.py` — `TradeEvent` (`:25`) / `QuoteEvent` (`:42`) gain the
   matching optional fields, defaulted so every existing construction call site stays valid
   unchanged.
3. `apps/backend/app/providers/historical.py` — both existing construction sites thread the new
   fields from `record` (the `RawTrade`/`RawQuote` instance already in scope) into the
   `TradeEvent`/`QuoteEvent` they build, when present: `HistoricalProvider.stream()` (`:70` quote /
   `:74` trade) and `ProgressiveHistoricalProvider._emit()` (`:134` quote / `:138` trade) —
   confirmed live: `record` in both loops already IS the `RawTrade`/`RawQuote` object, so this is
   a direct pass-through, not a new lookup.
4. `apps/backend/app/providers/adapters/alpaca.py` — both existing `RawTrade`/`RawQuote`
   construction sites populate the new fields from the real Alpaca SDK trade/quote response
   objects when the SDK provides them: `_fetch_one_subwindow` (`:369` trade / `:373` quote) and
   `_fetch_trades_quotes` (`:475` trade / `:479` quote). A third site exists in the live-streaming
   path (`:680`/`:684`) — spec scope is historical recording only; keep it consistent if trivial,
   do not let it pull in new plumbing.
5. `apps/backend/app/research/datasets.py` — `_event_to_row` (`:151`) / `_row_to_event` (`:172`)
   carry the new fields into/out of the stored JSON row ONLY when present — an event without them
   must serialize to the EXACT same row dict shape as before this change (no `"conditions": null`
   key ever emitted for an absent value; the `observer=`-kwarg precedent). `DatasetStore.record()`
   (`:404`) and `record_from_source()` (`:511`) gain optional `schema_basis: str | None = None` /
   `quote_size_unit: str | None = None` keyword params, stamped into `meta` (built at `:434`) only
   when supplied — every existing call site (none pass these) leaves the manifest shape
   byte-unchanged. A supplied `quote_size_unit` is validated against the EXISTING
   `micro_features.QUOTE_SIZE_UNITS` tuple (`micro_features.py:100` —
   `("shares", "round_lots", "unverified")`); do not define a second unit-vocabulary constant, and
   do NOT define `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`.
6. **This is the era's most dangerous change so far, per the iteration-6 evaluator.** Note for the
   developer: `_load()` (`datasets.py:252`) reads stored rows verbatim from disk and recomputes the
   checksum from THOSE stored rows — it never re-derives them through `_event_to_row` — so the 18
   real on-disk datasets are structurally safe from this diff as long as they are never rewritten
   (they are not). The actual risk surface is narrower than it looks: (a) `_row_to_event` handling
   an old row dict with no `conditions`/`exchange` key must default cleanly to `None`; (b)
   `_event_to_row` must never widen its emitted shape for a call site that still passes
   `conditions=None` (every existing call site, until J-06 steps 2-5 land the recorder).
7. Regression proof — re-run and report, not new test-writing: all 18 real tick datasets + every
   fixture under `tests/fixtures/datasets/` (2 files) and `tests/fixtures/alpaca/` (3 files) load
   byte-identically; `tests/test_observer_equivalence.py` and `tests/test_dense_replay_gate.py`
   (golden trace) pass byte-unmodified; `Config().config_fingerprint()` still prints
   `08e471b10130e1e2`.

### Backend — J-05: make the tick-family fold request reachable from a genuine production entry point

8. `apps/backend/app/research/walkforward.py` — new function (e.g. `run_tick_family_fold_request`)
   resolving REAL tick session dates via the EXISTING `_tick_dataset_session_dates` (`:984` —
   already resolves the real 11 ET dates 2026-05-27…2026-07-13, confirmed by the iter-6 audit's own
   live run) against a `DatasetStore(config.dataset_dir_resolved())`, then calling the
   ALREADY-WIRED `require_sufficient_sessions_for_folds(dates, DIAGNOSTIC_GEOMETRY)` (`:338`) —
   today this always raises `InsufficientSessionsForFoldsError` naming `11 < 105`, which IS the
   acceptance (T-7 "insufficient is an answer"). Developer's call whether to mirror the playbook
   path's register-then-check ordering (`register_fold_spec` at `:1138` before
   `require_sufficient_sessions_for_folds` at `:1148`) for ledger consistency — not mandated.
9. The CLI (`python -m app.research.walkforward`, `main()` at `:1197`) gains a new flag beside the
   existing `--diagnostic` (e.g. `--family tick_legacy`) calling the new function; on refusal,
   print + exit non-zero, mirroring the EXISTING `except InsufficientSessionsForFoldsError` block
   (`:1225-1228`) exactly — mirror the pattern, don't duplicate the print/exit logic.
10. Explicitly deferred: `POST /walkforward/compute`'s route-level family parameter — no UI/MCP
    consumer needs it yet.

### Verification — J-10 re-proof + required-still-passing

11. Full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/`, no extra `-q` —
    keeps the pass/skip/fail summary legible) ≥ iter-6's **3038 pass / 8 skip / 0 fail** baseline.
12. Frozen-foundation re-checks: `Config().config_fingerprint()` → `08e471b10130e1e2`; all 6
    `referee_*.py` SHA-256 hashes byte-identical to the iteration-0 baseline listing
    (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`); two consecutive `DatasetStore.replay()`
    calls over one unchanged legacy dataset yield byte-identical snapshot sequences.
13. Browser: clean `rm -rf apps/frontend/.next` + rebuild (T-9), store-scoped `:8301`/`:3301` rig,
    `journey-scripts/J-10.json`'s 13 steps (unmodified, byte-identical) — cockpit `/`,
    `/structure`, every shipped `/desk` section including the 3 Referee sections; plus
    required-still-passing regression for J-01 (Microscope Readiness) and J-02/J-03/J-04
    (deferred-budget acceptable ONLY if this iteration's diff provably cannot reach their served
    values — otherwise re-verify live, per the iter-5/iter-6 durability precedent). Read the LLM
    lane's OWN `...-ui-test-results.llm.md` verdict line directly — never trust the merged headline
    alone (see Notes: the iter-6 audit caught a `**FAIL**` markdown cell parsing as no-verdict and
    flipping a merged headline green; that framework bug is still unfixed).
14. Dev handoff at `docs/handoffs/goal-rapid-microscope-iter-7-dev.md` naming every fix with exact
    file:line anchors (TC-12 / DEFINITION OF DONE).

## Agents Required

- developer: yes -- implements items 1-14 above (provider/dataset schema additions, walkforward CLI
  wiring, tests, dev handoff). Zero frontend files, zero new `Config` field, zero new route (the
  J-05 fix is CLI-only; the J-06 step-1 fields are additive-only with no serving endpoint yet).

## Frontend Present

Frontend Present: yes

**Why, given zero frontend code changes this iteration:** confirmed working precedent from iter-6
(`iteration-state.md`: *"`Frontend Present: yes` WORKED — keep it"*, and the iter-6 audit: "The
browser lane genuinely dispatched for the first time in three iterations"). This flag is
machine-read by `scripts/automation/browser-qa-phase.sh`'s `detect_frontend_in_plan`, which greps
this plan for the literal string `frontend present: yes` and short-circuits the ENTIRE browser
lane — including the required-still-passing regression set (J-01-J-04) and the J-10 sentinel —
whenever it reads `no`. That silently cost two ESCALATE verdicts (iters 4 and 5). This iteration's
own diff touches zero `.tsx`/`.ts` files, adds no page, section, or control — this declaration is a
mechanical trigger for the QA lane, not a UI claim. The durable fix (reading the already-exported
`CHAIN_GOAL_TARGET_JOURNEYS` safeguard instead of gating on this one string) is
framework-maintenance work outside this agent's authority and outside `docs/goal.md`'s Key
Capabilities — flagged, not scheduled, in Notes below.

## UI Evolution

- New user-facing capability: **none.** No new page, section, button, or served field.
- New information displayed: **none.** No endpoint's response shape changes — `schema_basis` /
  `quote_size_unit` are written to the dataset manifest ONLY when a caller supplies them, and no
  caller does yet this iteration; `micro_snapshots.quote_size_unit_for_dataset()` already defaults
  an absent key to `"unverified"` (existing, unchanged code).
- New user actions: **none.** The new `--family tick_legacy` CLI flag is operator/CLI-only, not a
  UI control.
- UI surface changes: **none.**
- Navigation changes: **none.**
- What the browser pass actually verifies (regression only, not new capability): the **Microscope
  Readiness** section on `/desk` (J-01) and the full 13-step kept-product sentinel
  (`journey-scripts/J-10.json`, unmodified — cockpit `/` live tape + chart, `/structure` load +
  Tradable Map, every shipped `/desk` section including the 3 Referee sections). Both are
  pre-existing, already-shipped surfaces; this iteration adds no new element to either.

## Visual Requirements

Not applicable — no new component, layout, or visual state is introduced. Any styling diff would be
an unplanned regression, not a deliverable. The browser pass reuses the shipped dark-only, dense,
terminal-grade design as-is (no diff expected).

## Files to Create/Modify

- `apps/backend/app/providers/adapters/base.py` -- MODIFY: `RawTrade`/`RawQuote` gain optional
  preservation fields (conditions, exchange/venue, + whatever else the real SDK response carries).
- `apps/backend/app/providers/base.py` -- MODIFY: `TradeEvent`/`QuoteEvent` gain matching optional
  fields.
- `apps/backend/app/providers/historical.py` -- MODIFY: both construction sites (`stream()`,
  `_emit()`) thread the new fields through when present.
- `apps/backend/app/providers/adapters/alpaca.py` -- MODIFY: both existing historical construction
  sites (`_fetch_one_subwindow`, `_fetch_trades_quotes`) populate the new fields from the real SDK
  response when available.
- `apps/backend/app/research/datasets.py` -- MODIFY: `_event_to_row`/`_row_to_event` carry the
  fields present-only; `record()`/`record_from_source()` gain optional `schema_basis`/
  `quote_size_unit` kwargs, validated against `micro_features.QUOTE_SIZE_UNITS`.
- `apps/backend/app/research/walkforward.py` -- MODIFY: new tick-family fold-request function + new
  CLI `--family tick_legacy` flag mirroring the existing `--diagnostic` error handling.
- `apps/backend/tests/test_datasets.py` -- MODIFY: extend with round-trip + backward-compatibility
  tests (TC-1, TC-2, TC-3, TC-9).
- `apps/backend/tests/test_walkforward.py` -- MODIFY: extend the existing CLI-test block with the
  new tick-family path (TC-6, TC-7); leave `test_tc20_the_11_session_tick_corpus_returns_the_typed_
  floor_refusal_naming_11_lt_105` unmodified (TC-8).
- `docs/handoffs/goal-rapid-microscope-iter-7-dev.md` -- NEW: dev handoff naming every fix with
  exact file:line anchors.

Explicitly untouched (per phase spec OUT OF SCOPE / Do-Not-Redo): `micro_features.py`,
`micro_observer.py`, `micro_snapshots.py` (all three already implement the `quote_size_unit`
contract per J-02; touching any triggers a whole-corpus snapshot rebuild for zero benefit this
iteration — iter-3 lesson); `tick_recorder.py`, `vault.py`, universe registration, Tier-B
resolution, real Alpaca tranche recording (J-06 steps 2-5); `POST /walkforward/compute`'s family
parameter; `docs/goal.md`, `docs/rapid-validation-spec.md`, `blueprint.md`; any `.tsx`/frontend
file; any `Config` field; `journey-scripts/J-10.json` (reused byte-unmodified); the `_errors`-drop
in `_tick_dataset_session_dates` and the sealed-shard seed filter (both explicitly J-06-scope per
iter-6 audit finding B1/B2 and this phase spec's OUT OF SCOPE).

## Key Test Scenarios

(Condensed from the phase spec's own TC-1…TC-12 — cross-reference there for exact wording.)

- **TC-1** — all 18 real datasets + every committed fixture load byte-identically post-change
  (checksums verify, no new `conditions`/`exchange`/`schema_basis`/`quote_size_unit` key appears on
  any row or manifest that never had one).
- **TC-2** — a fresh `TradeEvent`/`QuoteEvent` carrying `conditions`/`exchange` (+ quote
  equivalents) round-trips through `record()` → `load_events()` exactly.
- **TC-3** — `record(..., schema_basis=..., quote_size_unit=...)` stamps both into the manifest
  verbatim; every pre-existing call site (no kwargs) leaves the manifest shape byte-unchanged.
- **TC-4** — `test_observer_equivalence.py` + `test_dense_replay_gate.py` pass byte-unmodified;
  fingerprint prints `08e471b10130e1e2`.
- **TC-5** — `test_real_data_gate.py` (Alpaca confinement) still passes; hermetic suite fetches no
  network.
- **TC-6** — the CLI's tick-family flag against a hermetic `tmp_path` (via
  `TAPEOLOGY_DATASET_DIR`) seeded with N < 105 tick fixtures prints a refusal containing the exact
  substrings `"{N} < 105"` and `"TR-15"`, exits non-zero, zero `ROW_KIND_FOLD_RESULT` rows written.
- **TC-7** — the SAME CLI path against the operator's real `.data/datasets` (11 real distinct
  dates) names exactly **"11 < 105"** — developer runs by hand, pastes the output into the dev
  handoff; the evaluator independently re-runs this same command against the real store.
- **TC-8** — `test_tc20_the_11_session_tick_corpus_returns_the_typed_floor_refusal_naming_11_lt_105`
  (the existing synthetic-date unit test) left unmodified, still passes.
- **TC-9** — grep this iteration's diff: no new `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` definition, no
  second `QUOTE_SIZE_UNITS`-shaped tuple.
- **TC-10** — full suite ≥ iter-6 baseline (3038 pass / 8 skip / 0 fail); 6 `referee_*.py` SHA-256
  hashes match the iteration-0 baseline; two consecutive `replay()` calls over one unchanged legacy
  dataset are byte-identical.
- **TC-11** — J-10 sentinel: clean `.next` rebuild, store-scoped rig, all 13 steps produce a
  screenshot (element capture for below-the-fold sections), the LLM lane's own verdict file reads
  PASS per step.
- **TC-12** — required-still-passing J-01/J-02/J-03/J-04 render previously-recorded served values,
  OR — if this diff changed a shared producer — the newly re-derived value proven live with a
  screenshot on record.

## Notes carried to developer/reviewer/QA/auditor

- **PUMP NOTE (standing, from the operator):** never pattern-based process kills (`pkill -f` /
  `killall`) for uvicorn/next/node/chrome/python — other projects share this host; kill only exact
  PIDs you started and recorded.
- **Iteration hygiene** (goal.md Constraints, "the era-6 retro"): keep browser acceptance narrow,
  default to the fixture-scoped backend for QA — this iteration already carries real risk in its
  backend diff; do not let QA scope creep add to the timeout risk that tripped 13 of 15 prior
  referee iterations.
- **Escalation flag — do not let this recur a 4th time.** This is the 4th consecutive full dispatch
  following an ESCALATE (iters 4, 5, 6 each returned ESCALATE again), now on a change the evaluator
  named as the era's most dangerous so far. Per the phase spec's own binding instruction: do NOT let
  the independent auditor step get budget-demoted — if a time crunch forces a choice, cut J-10
  sentinel re-verification depth before cutting the auditor's review of the byte-compat proof.
- **Known unfixed framework bug (not this iteration's scope):**
  `scripts/automation/merge_ui_test_results.py:64` accepts only bare `PASS`/`FAIL` tokens, so a
  markdown-emphasised `**FAIL**` browser-QA cell parses as no-verdict and a green merged headline
  can reach `status.json`/closure undetected (iter-6 audit finding E1 — caught only by the
  independent auditor reading the LLM lane's own file). Standing mitigation inside this loop: read
  the LLM lane's own verdict file directly (TC-11), never the merged headline alone. Needs a
  framework-maintenance session outside goal mode — flagged for the operator, not fixed in this
  product iteration's diff.
- **Two open owner rulings, non-blocking to this iteration's scope:** (1) the one-quote-early
  `micro_observer.py` depletion `available_at` timing stamp (`:636`/`:657`); (2) whether J-01's
  readiness photograph must show the real 12-symbol-day corpus when the store-scoped browser rig
  can only ever seed 2 PG fixture datasets (the rig's launcher structurally forbids pointing at the
  real `.data/datasets` store). Neither is touched by this iteration's scope.
- **J-06's OVERALL journey status is NOT claimed complete by this iteration** — only step 1 of 5.
  Steps 2-5 (`tick_recorder.py`, `vault.py`, universe registration, the Tier-B resolution order, the
  real Alpaca starter-tranche recording) remain outstanding; the evaluator determines J-05/J-10's
  resulting status, not the developer.
