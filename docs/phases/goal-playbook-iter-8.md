# Goal Iteration 8 — The evidence view + replay-scoping/defect carry items

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was `ESCALATE` (iteration 7); mandatory, no exceptions. This
  is also the first iteration whose target journey (J-08) pools every recorded signal into
  distributions — the class of honesty mistake the iter-4/5/6 audits caught three times and that
  is invisible in any screenshot, per the evaluator's own next-step recommendation.
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-10
- **Anti-goal reminders:**
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule and threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it; no code path iterates thresholds against outcomes (source-scan guard-tested); a threshold change is a spec revision + new signature, never an edit of recorded signals and never a sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice, imperative, prediction, probability, expectancy, edge, or significance language; the served registers state what was NOT measured (no fills, no costs, returns not stop-adjusted); `invalidation_price` is geometry, never an order concept. *(critical)*
  - **The evidence pools one signature.** Distributions never mix parameter regimes; other signatures are listed, not merged; the min-n floor tags, it never filters; truncated values never enter a pool undisclosed. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never overwritten; the store exposes no update or delete method (source-scan guard-tested). *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons, MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*

## GOAL

Ship J-08 "The evidence view" — a read-only, stat-cached endpoint and `/desk` section that pools
every recorded playbook signal at ONE signature into per-(setup, side, measure) distributions
beside the pooled baseline, honestly tagging low-n cells — and clear the five carry items the last
two ESCALATEs left open (replay-lane scoping, the missing J-06 golden, the owed Range Trade
re-capture, the back-scan plan's 500 on a half-typed date, and the J-05 replay assertion that can
false-pass on static copy).

## BACKGROUND

Iteration 7 shipped J-07 (the back-scan) but the engine's depth arbiter demoted its planned `full`
pass to `lean` for the third time this session, so no auditor read the first code that can write
many records into the operator's own store at once — the evaluator's own words: "the next journey
pools numbers into distributions, which is exactly where honest-measurement mistakes hide." Prior
verdict is `ESCALATE`, which per this agent's own binding rule (and the SPEED-20 arbiter lesson in
`lessons.md` iter-5: only `ESCALATE` reliably buys the auditor a seat) makes `full` depth mandatory
this iteration — no escape condition needed beyond the verdict itself. Target selection follows
rubric rule 3 (unblocker: J-08 is the natural next journey in the era's dependency order, explicitly
named by the iter-7 evaluator) and rule 6 (single risky journey: J-08 alone carries new pooling
math; the five carry items below are cheap, already-diagnosed defect/hygiene fixes, not a second
risky journey). Required-still-passing widens to ALL currently-passing journeys (J-01..J-07, J-10)
per the "widen on ESCALATE" rule, since a full pass is the right moment to refresh goldens and catch
selector drift session-wide.

Lessons applied: iter-3's scoped-store lesson and iter-6/7's split-scoping lesson (the
`resolve_desk_playbook_log_dir` universe-dir fallback) govern the evidence cache's own dir env var
and the replay-lane fix; iter-4's "silent-summary-copy invalidation" lesson means `EVIDENCE_REGISTER`
must be checked by the same copy-discipline guard pattern from day one; iter-5/6's degeneracy-check
lesson applies to any field definition this spec states that the canonical spec itself leaves open —
none does here, since J-08's acceptance text in `docs/goal.md` already fully specifies the cell shape
and the min-n constant (`PLAYBOOK_MIN_N_DISCLOSURE = 12`, already in
`docs/playbook-detector-spec.md:182`, zero diff needed).

Two owner rulings remain open (the §3.7 `range_trade` degenerate-trigger clarification, and the
three narrower-than-spec disclosures) and are explicitly OUT OF SCOPE again this iteration — they
are human-owned per rubric rule 6, not re-planned here.

## IN SCOPE

### Backend
- [ ] Build `app/research/desk_playbook_evidence.py`: reads recorded playbook records (via the
  existing `PlaybookStore`/`desk_playbook.py` reader, zero re-implementation), pools per-(setup,
  side, measure) value lists for the DEFAULT signature (the current `playbook_parameters()`'s own
  `compute_playbook_input_signature`), behind a derived, stat-keyed SQLite projection cache
  mirroring the `desk_meta_cache.py` contract (owns nothing, unopenable/deleted DB = cache miss,
  never a failed read; keyed off file stat, never file content).
- [ ] Wire `GET /research/desk/playbook/evidence` (optional `?signature=` to inspect a
  non-default signature's own `dates`/`created_span` WITHOUT pooling it) in `desk_routes.py`,
  matching the blueprint's already-reserved "Evidence aggregates" row.
- [ ] Fold: cells `{n, n_truncated, n_baseline, median_pct, p25_pct, p75_pct, mean_pct}` for
  signal vs. baseline side-by-side per (setup, side, measure); `invalidation_breached` counts by
  horizon; `below_min_n` tag under `PLAYBOOK_MIN_N_DISCLOSURE`; truncated values excluded from
  pools with the exclusion counted in `n_truncated`, never silently dropped; serve `register`
  (`EVIDENCE_REGISTER`, new module-level tuple, same pattern as `PLAYBOOK_REGISTER`).
- [ ] Extend `tests/test_copy_discipline.py` to cover `EVIDENCE_REGISTER` and the new page copy
  (no probability/expectancy/edge/significance/advice language).
- [ ] Extend `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` with every new served
  numeric the UI renders (median/p25/p75/mean/n/n_truncated/n_baseline/breached counts).
- [ ] Add a source-scan guard test proving the evidence cache class exposes no update/delete
  method and the pooling code never merges two signatures into one cell (mirrors the existing
  store-immutability and rail-import guard tests).
- [ ] Fix the back-scan plan defect: `GET .../backscan/plan` on a malformed/partial date (e.g.
  `2026-06-2`) returns an honest HTTP 200 empty/disclosed plan instead of an HTTP 500 — same
  status-code shape as the already-handled `from > to` case, never a debounce/UX change on the
  frontend (see Notes — assumption logged).
- [ ] Fix `journey-scripts/J-05.json`'s step-2 assertion so it targets a real signal-row-scoped
  selector/text instead of the word "Capitulation", which also appears in the section's own
  static description paragraph (per the iter-7 lesson: never assert on text that also lives in
  static copy).
- [ ] Record `journey-scripts/J-06.json` (a golden replay script for the range/double-top
  section) so J-06 stops being DEFERRED-BUDGET every time the time budget is tight.
- [ ] Scope the deterministic replay lane: extend (never rewrite)
  `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` forward as the mandatory
  launcher for every playbook golden-replay run (`J-01`..`J-08`, `J-10`'s playbook-touching
  steps), so no replay script can ever reach the operator's ambient `:8301`/real `.data/` store.

### Frontend
- [ ] Add the `/desk` **Playbook Evidence** section (below the shipped Backscan panel, per the
  blueprint's reserved IA slot): renders the served cells as a table (setup × side × measure),
  signal vs. baseline columns, `below_min_n` tag visible on tagged cells, `invalidation_breached`
  counts, and the `register` copy — no client-side arithmetic, every number a straight
  pass-through of the response.
- [ ] Re-take the owed Range Trade row screenshot (opened/expanded, full geometry line legible)
  on a freshly rebuilt scoped rig — the `evidence_makeup` item carried since iteration 6.

### New user-facing capability
The operator (and any browser-QA/screenshot pass) can now see, per setup family and side, how many
recorded signals fired, what their forward-return and max-drawdown distributions look like against
the pooled seeded-baseline anchors, and which cells are still too thin to trust — without any
manual computation.

### New information displayed
The Playbook Evidence table: per-(setup_id, side, measure) cell pairs (signal vs. baseline) with
`n`, `n_truncated`, `n_baseline`, `median_pct`, `p25_pct`, `p75_pct`, `mean_pct`; `below_min_n` tags;
`invalidation_breached` counts by horizon; other-signature listings (not pooled); the
`EVIDENCE_REGISTER` disclosure copy.

### New user actions
None beyond scrolling to the new section — per T-7 ("GETs never compute"), the evidence view is a
read-only fold of already-recorded data with no compute/refresh trigger of its own.

### UI surface changes
`/desk` gains one new section, **Playbook Evidence**, rendered below the shipped Backscan panel.
No existing section, route, or nav entry changes.

### Product surface delta
The Desk page now closes the loop from "what setups fired" (Playbook Signals) and "did we run every
session" (Backscan) to "what did those setups actually do" (Playbook Evidence) — still purely
descriptive, zero new statistics language. Separately, the Backscan plan preview stops erroring on
a half-typed date, and the deterministic replay lane can no longer reach the operator's real store.

### Blueprint conformance
`/desk` under the existing **Desk** nav section, in the IA slot the blueprint already reserved for
"Playbook Evidence — the per-(setup, side) distribution table beside the pooled baseline, min-n
tags (J-08, not yet built)" (`runs/goal-session-playbook/state/blueprint.md`). No nav-skeleton
change; the blueprint's Data-Contract "Evidence aggregates" row is updated in place (see below).

### Data-contract additions
**Evidence aggregates** — computed by `app/research/desk_playbook_evidence.py` (new); served by
`GET /research/desk/playbook/evidence` (already registered as a placeholder row in
`blueprint.md`; this iteration fixes its exact shape and flips "Ships at" from "not yet built" to
"J-08 (this iteration)"):

- `signature: string` — the pooled/default `compute_playbook_input_signature` value (verbatim from
  the existing playbook signature recipe, never re-derived).
- `cells: array<{setup_id: string, side: "long"|"short", measure: string (one of the rail's
  DESK_FORWARD_MEASURE_KEYS, e.g. "1m"/"5m"/"1h"/"4h"/"to_close"/"mdd_long"/"mdd_short"/etc.),
  signal: {n: int>=0, n_truncated: int>=0, median_pct: float|null, p25_pct: float|null,
  p75_pct: float|null, mean_pct: float|null}, baseline: {n_baseline: int>=0,
  median_pct: float|null, p25_pct: float|null, p75_pct: float|null, mean_pct: float|null},
  below_min_n: bool}>`
- `invalidation_breached: array<{setup_id: string, side: string, horizon: string,
  breached_count: int>=0, total_count: int>=0}>`
- `other_signatures: array<{signature: string, dates: array<string>,
  created_span: {from: string, to: string}}>` — listed, never pooled.
- `parameters: object` — the verbatim `playbook_parameters()` blob (provenance duty, same pattern
  as the existing playbook record payload).
- `register: array<string>` — `EVIDENCE_REGISTER` (new module-level constant tuple).

No existing Data-Contract row (bars, session honesty, measurement helpers, universe membership,
playbook records, compute progress, run ledger, back-scan plan/progress/ledger) is recomputed or
re-served a second way; this row reads the already-registered "Playbook records" row's own store
verbatim (file listing + measurement fields already on disk), matching the existing
"no second implementation" discipline the iter-7 coherence audit already confirmed for the
back-scan.

## OUT OF SCOPE

- J-09 (MCP contract v4 / 20 tools) — next iteration, per the natural dependency order.
- The two open owner rulings (§3.7 `range_trade` degenerate-trigger clarification; the three
  narrower-than-spec disclosures) — human-owned, not re-planned (rubric rule 6).
- Any statistics language (CIs, p-values, significance, expectancy, probability) — era-6 territory,
  explicitly a non-goal.
- Debouncing the Backscan plan preview's per-keystroke refetch — only the honest-response defect
  is fixed; the refetch cadence itself is a UX nicety, not named by any acceptance text.
- Any real, unscoped back-scan or playbook compute against the operator's live universe — every
  test/browser/replay act in this iteration runs on the scoped fixture rig only.
- Rewriting or deleting the iter-6 accidental real-store record
  (`.data/playbook/playbook-2026-08-07-84fcd116ebd7.json`) — kept per the "Do not redo" list and
  the immutable-data rail.
- Re-opening `desk_playbook_detect.py`'s detector logic — zero diff maintained this iteration.

## DEFINITION OF DONE

- [ ] J-08 passes via browser-qa-agent (one well-populated cell and one `below_min_n`-tagged cell
  legible in a single screenshot)
- [ ] Required-still-passing journeys J-01..J-07 and J-10 remain green (deterministic replay lane,
  now scoped, plus LLM fallback where a golden is missing/stale)
- [ ] No anti-goal violation introduced — evidence pools exactly one signature; no
  probability/expectancy/advice language in `EVIDENCE_REGISTER` or the new section copy; the
  evidence cache exposes no update/delete method
- [ ] Full backend suite passes with zero regressions: exit 0, passed count ≥ 2130, 8 skipped (the
  iter-7 evaluator-verified floor), `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`
- [ ] Back-scan plan endpoint returns an honest HTTP 200 (never HTTP 500) on a malformed/partial
  date
- [ ] `journey-scripts/J-06.json` exists and passes a deterministic replay on the scoped rig
- [ ] `journey-scripts/J-05.json`'s assertion targets a real signal row, not static section copy
- [ ] The deterministic replay lane launches/targets the scoped fixture backend for every
  playbook-touching golden script (verified: zero new files under the operator's real
  `apps/backend/.data` during a replay run)
- [ ] Owed Range Trade row re-capture delivered (evidence_makeup cleared)
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-8-dev.md`

## TESTING REQUIREMENTS

- Browser: J-08 (new); replay-verify J-01, J-02, J-03, J-04, J-06, J-07, J-10 on the scoped rig;
  live-browser-verify J-05 (its replay script changes this iteration, so a fresh live pass
  confirms the new assertion before it is trusted as a golden).
- Unit/integration: evidence pooling math (hand-computed fixture aggregate), cache cold/warm
  byte-identity, cache-deleted rebuild, min-n tagging, truncation-exclusion, single-signature
  pooling, copy-discipline lint, source-scan guards (no update/delete method, no cross-signature
  merge, no second rail implementation), back-scan plan malformed-date handling.
- Error cases: malformed/partial date to `.../backscan/plan` (honest 200, not 500); a
  (setup, side, measure) cell with zero recorded signals (served as `n: 0`, not omitted, not a
  crash); a signature with recorded records but not the current default (listed under
  `other_signatures`, never folded into `cells`).

Test-first contract:

- TC-1: given a scoped fixture rig with 3 recorded playbook records at the current signature
  containing a mix of jbe/dbi/capitulation/range_trade signals, when
  `GET /research/desk/playbook/evidence` is called with the cache cold, then the response body's
  cell for `(setup_id="jbe", side="long", measure="1h")` has `signal.n`, `signal.n_truncated`,
  `baseline.n_baseline`, `signal.median_pct`, `signal.p25_pct`, `signal.p75_pct`,
  `signal.mean_pct` matching a hand-computed aggregate over exactly those recorded signals.
- TC-2: given the same fixture set unchanged since TC-1, when the same GET is called again with
  the cache now warm, then the response body is byte-identical to TC-1's response.
- TC-3: given a fixture recorded set where cell `(setup_id="dbi", side="short", measure="4h")` has
  fewer than 12 (`PLAYBOOK_MIN_N_DISCLOSURE`) recorded signals, when the evidence endpoint is
  called, then that cell's JSON carries `below_min_n: true` while `median_pct`/`p25_pct`/
  `p75_pct`/`mean_pct` are still populated (not null, not omitted).
- TC-4: given a fixture set containing one signal with `n_truncated > 0` for a given cell, when the
  evidence endpoint is called, then that cell's `signal.n_truncated` is > 0 and the hand-computed
  aggregate proves the truncated value is excluded from `median_pct`/`mean_pct`'s underlying pool.
- TC-5: given two distinct playbook input signatures both present in the fixture store (current
  default plus one older), when GET evidence is called with no `?signature=` override, then
  `cells` pools ONLY the default signature's records, and the older signature appears in
  `other_signatures` with its own `dates` and `created_span`, never merged into any cell.
- TC-6: given the evidence projection cache DB file is deleted from disk before the request, when
  GET evidence is called, then the response body is byte-identical to a pre-deletion capture of
  the same request (latency may differ, content does not).
- TC-7: given the fixture set, when GET evidence is called, then `register` (`EVIDENCE_REGISTER`)
  contains no word from {probability, expectancy, edge, significance, advice, prediction} (copy
  lint) and states baseline = seeded random anchors, no fills, no costs.
- TC-8: given the `/desk` page loaded on the scoped fixture rig with playbook records present,
  when the operator scrolls to the new Playbook Evidence section, then one cell with `n >= 12`
  (not `below_min_n`) and one cell with `below_min_n: true` are both legible in a single
  screenshot with their numeric fields visible, matching the served JSON verbatim.
- TC-9: given the Backscan plan endpoint, when
  `GET .../backscan/plan?from=2026-06-2&to=2026-06-24` is called (a half-typed `from` date), then
  the response is HTTP 200 with an honest empty/disclosed plan body, never HTTP 500.
- TC-10: given the `/desk` Backscan panel's From date box mid-typed to `2026-06-2`, when the panel
  auto-refetches the plan preview, then no raw 500/error banner is shown (consistent with TC-9's
  response).
- TC-11: given the deterministic golden-replay lane is invoked for the playbook journeys, when it
  starts, then it launches/targets the scoped fixture backend
  (`qa_playbook_iter7_fixture_scoped_backend.sh` or its iter-8 extension), verified by
  `find apps/backend/.data -newermt "<run start>" -type f` returning zero playbook/backscan
  record or ledger files after the run.
- TC-12: given `journey-scripts/J-06.json` did not exist before this iteration, when the iteration
  completes, then the file exists and a deterministic replay run against the scoped rig returns
  PASS for it.
- TC-13: given `journey-scripts/J-05.json`'s prior step-2 asserted the substring "Capitulation"
  (also present in the section's static description paragraph), when this iteration completes,
  then the script asserts on a selector/text scoped to a real signal row instead, and a
  deliberately fixture-mismatched replay run (wrong symbol seeded) causes the script to FAIL,
  proving the new assertion discriminates real evidence from static copy.
- TC-14: given the Range Trade row on the scoped fixture rig's Playbook Signals section, when the
  operator opens/expands the row on a freshly rebuilt (`rm -rf .next`) rig, then a fresh
  screenshot captures its full geometry disclosure line (range MBR width, zone touches, broke-at
  slot, crossed-midrange) legible in one image.
- TC-15: given the full backend test suite, when run to completion on the scoped rig, then it
  exits 0 with passed count ≥ 2130 and 8 skipped, and `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`.

## NOTES

- Assumption logged to `runs/goal-session-playbook/state/assumptions.md` (iter-8 — goal-decomposer):
  the malformed-date fix's exact response shape (HTTP 200 empty/disclosed plan, mirroring the
  already-handled `from > to` case) rather than an HTTP 4xx, since neither `docs/goal.md` nor the
  canonical spec states a status code for this case and T-5 ("fail closed, disclose the absence")
  is the closest governing rail.
- Depth is `full` because the prior verdict is `ESCALATE` — this agent's binding rule, independent
  of the engine's own depth-arbiter demotion history noted in `lessons.md` iter-5.
- Required-still-passing is widened to all 8 currently-passing/partial journeys (J-01..J-07, J-10)
  per the "widen on ESCALATE" guidance — this is also the natural moment to refresh J-05's and
  J-06's goldens.
- The auditor should read the new pooling code end-to-end against a hand-built fixture, per the
  evaluator's explicit request — this is exactly the class of mistake (silent cross-signature
  pooling, a min-n filter instead of a tag, a truncated value slipping into a mean) that three
  prior audits caught and no other lane would see in a screenshot.
