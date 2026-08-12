# Goal Iteration 12 — Evidence cells disclose the basis of their own n (J-11)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 12
- **Mode:** next
- **Depth:** lean
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07, J-08, J-09, J-10
- **Frontend Present:** yes
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins
    are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is
    an explicit, logged act. *(critical)*
  - **Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule
    and threshold exists in [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) BEFORE
    the code that uses it; no code path iterates thresholds against outcomes (source-scan
    guard-tested); a threshold change is a spec revision + new signature, never an edit of
    recorded signals and never a sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - **The evidence pools one signature.** Distributions never mix parameter regimes; other
    signatures are listed, not merged; the min-n floor tags, it never filters; truncated values
    never enter a pool undisclosed. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.**
    New signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
    inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys,
    this Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth acceptance criterion, keep the `default` profile and `v1`
    byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey
    just to keep the loop alive is a failure. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
    the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Every Playbook Evidence cell on `/desk` states the size of the pool its numbers actually rest on —
how many of the setup's recorded signals were truncated versus genuinely unmeasurable at that
horizon, how many distinct sessions contributed, and which recorded dates the whole pooled table is
built from — so a thin-looking `n` (like `double_top:short` at `1m`) is legible as "59 of 90 signals
were unmeasurable there," never mistaken for a small sample.

## BACKGROUND

Iteration 11 closed the era GOAL_ACHIEVED with all ten Must-have journeys passing, but the engine
dispatched it as an **evidence-only** pass, so two of its own three planned items were never built
(`lessons.md` iter-11: "A `Depth: evidence` micro-path silently deletes planned code work... Never
plan code work under it"). The goal-proposer then appended **J-11** inside `docs/goal.md`'s
`AUTO:journeys` marker: the evidence fold's served `n` silently drops two exclusion classes without
counting them (`desk_forward.py:596`'s `if measure["return_pct"] is None: continue`, and
`desk_playbook_evidence.py:315`'s `_baseline_truncated` computed and thrown away) while
`EVIDENCE_REGISTER` promises "the exclusion counted, never silently dropped," and the pooled
signature never states the dates it pools even though every `other_signatures` entry already does.
I read the current source directly (both line numbers confirmed unchanged) rather than trusting the
journey text on faith.

This iteration targets J-11 alone — nothing else is failing or regressed (all ten journeys
`passing`, 0 regressed, `coherence.md` iter-11 = `COHERENCE-PASS`). Depth is **lean**, matching the
engine's binding recommendation: I checked all four escape conditions myself and none holds — prior
verdict is `GOAL_ACHIEVED` (not ESCALATE/REGRESSION), the last coherence audit `PASS`ed, only 1 of
the 6-iteration hardening-cadence window has elapsed, and J-11 is explicitly NOT a brand-new
full-stack journey in the sense that trigger describes: `docs/goal.md`'s own J-11 text insists this
is a purely additive enrichment of the ALREADY-shipped "Evidence aggregates" row/endpoint — no new
row, no new owner, no new endpoint, no cache-schema change, no bar read, no call into
`_measure_from`. I independently confirmed this by reading `desk_playbook_evidence.py` end to end:
every new count is derivable from data `PlaybookEvidenceCache`'s per-file projections already store
(`session_date`, `recorded_at`, full `forward` leaves), and the route (`desk_routes.py:1320`)
returns a plain `dict` with no `response_model`, so new keys flow through with zero route diff.

Two of the three carried, disclosed-not-fixed items from iteration 10/11 ride along as cheap
passengers (see `runs/goal-session-playbook/state/assumptions.md` iter-12 entry for the full
reasoning): the Playbook Signals session-date input's invalid-state border (`page.tsx:5591`, an
equal-specificity Tailwind collision between `ASOF_INPUT_CLASS`'s `border-slate-700` and the
conditionally-appended `border-amber-500` — confirmed still present, and confirmed NOT shared with
the Backscan/Deep-backfill From/To inputs at lines 3412/3425/3608/3621, which never had this
affordance, nor with the Refresh Data From/To inputs at lines 4411/4427, which share the SAME
collision but stay untouched per the iter-11 decomposer's own scoping decision) and the
`TAPEOLOGY_BAR_INDEX_DB` fifth scoping-guard entry (`desk_playbook_backscan.py`'s
`_SCOPING_ENV_VARS`, confirmed still exactly four vars). Both are single-call-site/single-tuple-entry
fixes with zero risk to J-11's own diff. The third carried item — a false `"new": true, "verified":
true"` claim plus nonexistent `role=tab` clicks in `reports/phase-goal-playbook-iter-11-demo.json`
— is a historical showcase artifact, not source code; it stays OUT OF SCOPE for this spec (see
NOTES) since J-11's own acceptance text already binds THIS iteration's own demo-narrator step to not
repeat the mistake.

Applicable lessons carried forward: (1) zero diff to `desk_forward.py` — every new count reuses its
`_collect_measures` output rather than adding a return value to that function; (2) T-11 (replay-script
collisions) — the new basis line must sit BESIDE the existing "Built from signature:" text
(`J-09.json`'s own assertion) without altering it, and no existing `desk-evidence-cell-row` content
that `J-08.json` matches on may change; (3) the iter-6 lesson that a behavior-only fix can leave
`playbook_input_signature` unmoved while changing served content — confirmed moot here since J-11's
new fields are served-only and never enter `playbook_parameters()`.

## IN SCOPE

### Backend
- [ ] Extend `desk_playbook_evidence.py`'s cell fold (`_fold_cells`, `_signal_cell`, `_baseline_cell`)
      to serve, per cell: `signal.n_unmeasured`, `signal.n_sessions`, `baseline.n_truncated`,
      `baseline.n_unmeasured`, `baseline.n_sessions` — reusing `desk_forward._collect_measures`'s
      already-returned `(values, n_truncated)` tuple and the per-projection `session_date` the cache
      already stores; zero diff to `desk_forward.py`; zero change to `PlaybookEvidenceCache`'s SQL
      schema or to `_file_projection`'s shape.
- [ ] Extract the per-signature dates/created-span/record-count logic `_fold_other_signatures`
      already computes into one shared helper; call it once per `other_signatures` entry (which
      gains `n_records`) and once more, over `default_projections`, to build a new payload-level
      `basis: {dates, n_records, created_span}` block returned from `fold_evidence`.
- [ ] Update `EVIDENCE_REGISTER` so its exclusion-disclosure sentence explicitly covers the
      unmeasurable class, the baseline's own truncated/unmeasured counts, and names the basis
      block — copy stays descriptive, no probability/expectancy/edge/significance language
      (`test_copy_discipline.find_violations` stays clean).
- [ ] Passenger: add `"TAPEOLOGY_BAR_INDEX_DB"` as a fifth required entry in
      `desk_playbook_backscan.py`'s `_SCOPING_ENV_VARS`, and update the guard's raised-error message
      and docstrings from "four" to "five" vars accordingly. `_assert_scoped` stays test/browser-QA
      rig-only, never called from a live HTTP route (unchanged).

### Frontend
- [ ] `apps/frontend/lib/types.ts`: add the five new count fields to
      `DeskPlaybookEvidenceCellStats`/`DeskPlaybookEvidenceBaselineStats`, add `n_records` to
      `DeskPlaybookEvidenceOtherSignature`, add a new `DeskPlaybookEvidenceBasis` interface, and wire
      `basis: DeskPlaybookEvidenceBasis` onto `DeskPlaybookEvidence`.
- [ ] `apps/frontend/app/desk/page.tsx`'s Playbook Evidence section: render a new basis line beside
      the existing "Built from signature:" line (new `data-testid`, e.g. `desk-evidence-basis`;
      the existing signature line's text stays byte-unchanged) and the five new per-cell counts in
      the cells table (new `data-testid`s only) — no client-side arithmetic anywhere; `lib/api.ts`
      picks up the enriched shape automatically (pure pass-through fetch, no logic change expected).
- [ ] Extend `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` to cover every new served
      numeric actually referenced in the new JSX (following the established `cell.signal.*`/
      `cell.baseline.*` naming convention), plus a seeded counter-test proving the extended pattern
      can catch a violation (the "a lint that cannot fail proves nothing" precedent).
- [ ] Passenger: fix the Playbook Signals session-date input's invalid-state border
      (`page.tsx` ~line 5591, `data-testid="desk-playbook-date-input"`) so an invalid value renders
      an amber border, scoped to that ONE input's own `className` expression only —
      `ASOF_INPUT_CLASS` itself, the Refresh Data / Backscan / Deep-backfill From/To inputs, and
      every other call site stay byte-unchanged.

### New user-facing capability
The owner can now tell, for any evidence cell, how much of its pooled signal set was actually
usable versus recorded-but-unmeasurable at that horizon (and, separately, truncated), how many
distinct sessions it draws from, and — for the pooled table as a whole — exactly which recorded
dates and how many records it is built from.

### New information displayed
Per cell: `n_unmeasured` and `n_sessions` beside the signal side's existing `n`/`n_truncated`;
`n_truncated`, `n_unmeasured`, and `n_sessions` beside the baseline side's existing `n_baseline`.
At the top of the section: a basis line stating the pooled/default signature's own record count,
contributing dates, and created-at span.

### New user actions
None — the section stays a read-only, scroll-only GET view (T-7: GETs never compute); no new
button or control. (Passenger, unrelated to J-11: the Playbook Signals date input now visibly
reddens/ambers on an invalid value instead of staying grey.)

### UI surface changes
The existing `/desk` Playbook Evidence section gains one new header line and five new columns/
values in its existing cells table. The existing Playbook Signals section's session-date input
changes border color on error only.

### Product surface delta
No new page, no new nav entry, no new route. The already-shipped `/desk` Playbook Evidence section
becomes more legible about its own denominator; every other shipped `/desk`/`/structure`/`/`
surface renders exactly as shipped.

### Blueprint conformance
`/desk` → Playbook Evidence section — J-08's existing Information Architecture home
(`runs/goal-session-playbook/state/blueprint.md`, "Navigation skeleton" + "Feature / journey homes"
table, J-08/J-11 rows). No new page, no nav-skeleton edit; blueprint updated additively this
iteration (new J-11 row + iteration-12 status paragraph + the "Evidence aggregates" Data Contract
row's "Ships at" column).

### Data-contract additions
All seven fields below extend the ALREADY-registered **"Evidence aggregates"** row — same owner
(`app/research/desk_playbook_evidence.py`), same serving endpoint
(`GET /research/desk/playbook/evidence`) — no new row, no new owner, no new endpoint:

- `cells[].signal.n_unmeasured: int >= 0` — count of this cell's pooled signal events whose
  relevant horizon leaf carries `return_pct: null` (e.g. a `1m` measure on a 5m-basis session).
- `cells[].signal.n_sessions: int >= 0` — count of distinct recorded `session_date`s that
  contributed ≥1 signal event to this cell's pool.
- `cells[].baseline.n_truncated: int >= 0` — the baseline pool's own truncated-value count
  (already computed as `_baseline_truncated`, previously discarded).
- `cells[].baseline.n_unmeasured: int >= 0` — the baseline-pool mirror of `signal.n_unmeasured`.
- `cells[].baseline.n_sessions: int >= 0` — the baseline-pool mirror of `signal.n_sessions`.
- `other_signatures[].n_records: int >= 1` — record count for that named (non-default) signature,
  from the same shared per-signature summarizer helper the `basis` block below reuses.
- `basis: { dates: string[]; n_records: int >= 0; created_span: { from: string; to: string } | null }`
  — a NEW top-level payload key: the pooled/default signature's own contributing dates, record
  count, and created-at span (`created_span: null` iff `n_records == 0`).

## OUT OF SCOPE

- Any change to `desk_forward.py` (zero diff, era-wide invariant) — new counts are derived from its
  already-returned `_collect_measures` output only.
- Any change to `desk_playbook.py`, `desk_playbook_detect.py`, `desk_playbook_features.py`, or
  `PlaybookStore`'s schema — detection/measurement logic and the record store are untouched; no
  playbook record is written, rewritten, backfilled, or re-keyed.
- Any change to `PlaybookEvidenceCache`'s SQL schema, `_file_projection`'s shape, or a cache
  migration of any kind — every new value folds from data the cache already stores.
- Any change to `GET /research/desk/playbook` (the "Playbook records" row/endpoint) or the compute/
  back-scan routes — only the "Evidence aggregates" endpoint changes.
- Any change to `docs/playbook-detector-spec.md` — the evidence fold's count/basis math is
  presentation of already-recorded measurements, not detector formation/trigger/invalidation logic.
- Any new `Config` field or fingerprint movement — `08e471b10130e1e2` stays pinned.
- The Refresh Data From/To inputs' identical border collision (`page.tsx:4411/4427`) and the
  Backscan/Deep-backfill From/To inputs (never had the amber affordance) — explicitly untouched,
  carried per the iter-11 decomposer's own scoping decision.
- Correcting or re-recording `reports/phase-goal-playbook-iter-11-demo.json` — a historical showcase
  artifact, not source code; flagged in NOTES, not built here.
- Any statistics, probability, significance, or edge/expectancy language anywhere (era-6 "The
  Referee" territory) — the new fields are exclusion COUNTS only.
- Any PnL, R-multiple, or promotion-ledger involvement — the playbook measures no PnL.

## DEFINITION OF DONE

- [ ] J-11 passes via browser-qa-agent: the basis line and a visible `n_unmeasured > 0` cell are
      captured by screenshot on the scoped fixture rig after a T-9 clean rebuild (TC-12).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-07, J-08, J-09, J-10 remain green via
      deterministic replay (LLM fallback only where a golden is missing) (TC-13, TC-16).
- [ ] No anti-goal violation introduced: single source of truth holds (one owner/endpoint for every
      new field), no second measurement-rail implementation, no evidence pooling across signatures,
      no record file rewritten, no threshold/statistics language added (TC-6, TC-9, TC-10,
      TC-11, TC-16).
- [ ] Unit tests pass; no regressions in `test_desk_playbook_evidence.py`'s existing
      (that file's own) TC-1..TC-7 tests or `test_desk_playbook_backscan.py`'s existing (that
      file's own) TC-13 tests — mapped, in THIS spec's TC- numbering below, to TC-1 through
      TC-9 (new evidence-fold cases) and TC-15 (backscan-guard extension).
- [ ] Full backend suite green at or above the iter-11 floor (2168 passed / 8 skipped), pin
      `08e471b10130e1e2` unchanged, MCP `list_tools()` still exactly 20, the `desk_playbook_evidence`
      byte-identical-proxy MCP test still green with the enriched body (TC-16).
- [ ] Passenger fix landed: the Playbook Signals date input shows an amber border on an invalid
      value, scoped to that one input only (TC-14).
- [ ] Passenger fix landed: `_SCOPING_ENV_VARS` holds five vars including `TAPEOLOGY_BAR_INDEX_DB`,
      with a genuine negative counter-test on the fifth var alone (TC-15).
- [ ] This iteration's own demo-narrator walkthrough step for the enriched Playbook Evidence section
      is `[NEW]`-flagged and `verified: true` ONLY if actually built and captured against real
      rendered output — no repeat of iteration 11's false claim (TC-17).
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-12-dev.md` (plus a `-frontend.md`
      handoff, per this session's established convention for iterations with frontend work) (TC-18).

## TESTING REQUIREMENTS

- Browser: J-11 (Playbook Evidence basis line + `n_unmeasured > 0` cell, screenshot); regression
  smoke via deterministic replay for J-01, J-02, J-03, J-07, J-08, J-09, J-10.
- Unit/integration: `apps/backend/tests/test_desk_playbook_evidence.py` (new cases below, extending
  the existing TC-1..TC-7 fixture style — hand-crafted `PlaybookStore` records via `_record`/
  `_signal`/`_forward`, never a real detector walk); `apps/backend/tests/test_desk_playbook_backscan.py`
  (TC-13 extension); `apps/backend/tests/test_desk_ui_guards.py` (guard extension + counter-test);
  `test_copy_discipline.py` coverage of the updated `EVIDENCE_REGISTER`; full backend suite.
- Error cases: an entirely empty store still serves `basis: {"dates": [], "n_records": 0,
  "created_span": null}` and every cell's new fields at `0`, never omitted or fabricated; a cell
  whose baseline pool is empty serves all three new baseline counts as `0`, not null or absent; an
  `_assert_scoped` call missing only the fifth env var raises `PlaybookNotScopedError` naming it.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given a hand-crafted signal whose `forward` leaf was built on a 5m-basis session (so
  `horizons["1m"]["return_pct"]` is null, "finer than the 5m touch series") pooled alongside another
  signal whose `1h` leaf IS measurable, when `fold_evidence` is called, then that (setup, side, "1m")
  cell serves `signal.n == 0`, `signal.n_truncated == 0`, `signal.n_unmeasured == 1`, while the same
  (setup, side, "1h") cell serves `signal.n_unmeasured == 0`.
- TC-2: given three pooled signals for one (setup, side) — one untruncated, one truncated
  (`_truncated_forward`), one unmeasurable at `"1h"` — when `fold_evidence` is called, then the
  `"1h"` cell's `signal.n + signal.n_truncated + signal.n_unmeasured == 3` exactly, its
  `"mdd_long_1h"`/`"mdd_short_1h"` sibling cells serve the IDENTICAL three counts (not independently
  recomputed), and the `"to_close"`/`"mdd_long"`/`"mdd_short"` (session-level) cells for the same
  pool serve `signal.n_unmeasured == 0` regardless.
- TC-3: given `baseline_anchors` planted for one pool key including one truncated and one
  unmeasurable-at-`"1h"` anchor (3 total), when `fold_evidence` is called, then
  `baseline.n_truncated` and `baseline.n_unmeasured` are wired (not both `0` by omission) and
  `baseline.n_baseline + baseline.n_truncated + baseline.n_unmeasured == 3` for the `"1h"` cell.
- TC-4: given four `PlaybookStore` records at the current signature on four distinct
  `session_date`s, three of which each contribute exactly one (jbe, long) signal and the fourth
  contributing only OTHER setups, when `fold_evidence` is called, then the (jbe, long) cell's
  `signal.n_sessions == 3` (not 4).
- TC-5: given three records at the current/default signature across three distinct dates, when
  `GET /research/desk/playbook/evidence` (or `fold_evidence`) is called, then
  `payload["basis"] == {"dates": <the 3 dates, sorted>, "n_records": 3, "created_span": {"from":
  ..., "to": ...}}`, and `basis["dates"]`/`basis["created_span"]` are byte-identical to
  `inspect_signature(store, that_same_signature)`'s own `dates`/`created_span` for the SAME
  signature.
- TC-6: given one record at an OLDER, non-default signature, when `fold_evidence` is called, then
  its `other_signatures` entry now also serves `n_records: 1` alongside its existing `signature`/
  `dates`/`created_span`, unchanged otherwise.
- TC-7: given an entirely empty store, when `fold_evidence` is called, then `basis == {"dates": [],
  "n_records": 0, "created_span": None}` and every cell's `signal.n_unmeasured`/`signal.n_sessions`/
  `baseline.n_truncated`/`baseline.n_unmeasured`/`baseline.n_sessions` read `0` (the full declared
  cross product, never an omitted key — mirrors the existing zero-signals precedent).
- TC-8: given the projection cache cold, then warm, then rebuilt after deleting the cache DB file,
  when `fold_evidence` is called each time, then the FULL enriched body (including all seven new
  fields) is byte-identical across all three reads (extends the existing TC-2/TC-6 precedent).
- TC-9: given the exact fixtures already used by `test_desk_playbook_evidence.py`'s current TC-1
  through TC-7, when `fold_evidence` is called after this iteration's diff, then every PRE-EXISTING
  served number (`n`, `median_pct`, `p25_pct`, `p75_pct`, `mean_pct`, `below_min_n`, breach counts)
  is numerically unchanged from its recorded pre-iteration value.
- TC-10: given `_PRICE_ARITHMETIC_FIELDS` extended for every new served numeric referenced in the
  new JSX, when a seeded violation (e.g. `cell.signal.n_unmeasured - cell.signal.n`) is scanned,
  then the pattern matches (the guard CAN fail), and when the real `apps/frontend/app/desk/page.tsx`
  source is scanned, then zero matches are found.
- TC-11: given the updated `EVIDENCE_REGISTER`, when `test_copy_discipline.find_violations` scans
  it, then zero forbidden-language violations are returned, and the sentence textually names the
  unmeasurable class, the baseline's truncated/unmeasured counts, and the basis disclosure.
- TC-12: given the scoped fixture rig seeded with a session whose `1m` leaves are recorded
  unmeasurable, after a T-9 clean rebuild, when a real browser opens `/desk` and scrolls to Playbook
  Evidence, then a new basis line is visible beside "Built from signature:" (new `data-testid`) and
  at least one visible cell row shows `n_unmeasured > 0` beside its own `n` — captured by screenshot.
- TC-13: given the existing golden scripts `journey-scripts/J-08.json` and `journey-scripts/J-09.json`,
  when replayed against the post-iteration build, then both still PASS unmodified — `J-09.json`'s
  `"Built from signature:"` substring match and `J-08.json`'s two `desk-evidence-cell-row`
  CSS-selector matches both still resolve.
- TC-14: given the Playbook Signals session-date input filled with `"not-a-date"`, when the
  component re-renders, then its resolved border color is amber (not grey), `aria-invalid="true"`
  and the visible error text are unchanged from today, and `ASOF_INPUT_CLASS` plus every other
  `ASOF_INPUT_CLASS` call site (Refresh Data From/To, Backscan From/To, Deep-backfill From/To) stay
  byte-unchanged in source.
- TC-15: given `_SCOPING_ENV_VARS` extended to five entries, when `_assert_scoped(root)` is called
  with all five vars set to paths rooted under `root` and outside any `.data/` directory, then it
  does not raise; when called with only `TAPEOLOGY_BAR_INDEX_DB` unset (the other four set the
  same way), then it raises `PlaybookNotScopedError` naming that var; source-scan confirms
  `_assert_scoped` has no caller under `desk_routes.py`.
- TC-16: given the full backend suite, when run to completion, then it exits 0 with pass count at or
  above 2168 (8 skipped), `Config().config_fingerprint()` reads `08e471b10130e1e2`,
  `app.mcp.list_tools()` reports exactly 20 tools, the `desk_playbook_evidence` MCP byte-identical-
  proxy tests pass against the enriched body, and every previously-recorded playbook JSON file's
  SHA-256 is unchanged from before this iteration.
- TC-17: given this iteration's own demo-narrator run, when it generates
  `reports/phase-goal-playbook-iter-12-demo.json`, then every step whose `"new": true`/
  `"verified": true` targets the enriched Playbook Evidence section (the basis line or any new
  count) is checked against a real, already-captured screenshot/DOM state showing that exact
  content rendered, and no step's action targets a `role=tab` (or other) element that does not
  exist on `/desk`.
- TC-18: given the iteration completes, when `docs/handoffs/` is listed, then
  `goal-playbook-iter-12-dev.md` and `goal-playbook-iter-12-frontend.md` both exist.

## NOTES

- **Implementation caution (not a code mandate):** `n_unmeasured` must be keyed on the underlying
  horizon LABEL's `return_pct is None` fact, shared identically across that label's return measure
  and its two `mdd_long_{label}`/`mdd_short_{label}` siblings (TC-2) — NOT derived independently
  per measure key via naive `len(events) - len(values) - n_truncated` subtraction, since an MDD
  sibling's own value list can in principle be shorter than its return sibling's for a reason
  unrelated to unmeasurability (a pre-per-horizon-MDD legacy leaf missing `mdd_long_pct`/
  `mdd_short_pct`) — never observed in playbook data today (the playbook was born after the dual-MDD
  rail existed) but not provably impossible, and a subtraction-only implementation would silently
  get it wrong the day it is.
- **Showcase artifact flag, not this iteration's code:** `reports/phase-goal-playbook-iter-11-demo.json`
  step 2 falsely tags an unbuilt fix `"new": true, "verified": true` with a fabricated `"Invalid
  date"` expectation, and steps 5/6 click `role=tab` targets `/desk` does not have. This is carried
  forward, unfixed, as a historical-artifact honesty defect for whoever next regenerates or
  publishes this era's showcase materials — not built in this spec (see OUT OF SCOPE). This
  iteration's OWN demo-narrator output must not repeat it (DEFINITION OF DONE).
- Applied lessons: `lessons.md` iter-11 ("`Depth: evidence` deletes planned code work") — this spec
  is explicitly `Depth: lean`, not evidence, so developer+reviewer are dispatched for real; iter-9
  ("T-11 replay-script collisions") — TC-13 pins that the two existing goldens touching this section
  keep passing unmodified; the era-wide "zero diff to `desk_forward.py`" invariant — reflected in
  every backend IN SCOPE bullet and OUT OF SCOPE line above.
- Assumption-ledger entry written: `runs/goal-session-playbook/state/assumptions.md` iter-12 —
  which of the three carried items ride as passengers here and why.
- Blueprint updated additively this iteration (no nav-skeleton change, no re-approval needed): new
  "STATUS AS OF ITERATION 12" paragraph, a new J-11 row in "Feature / journey homes", and the
  "Evidence aggregates" Data Contract row's "Ships at" column extended.
