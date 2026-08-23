# Goal Iteration 26 — Close the 9-golden coverage gap; fix the desk-readiness cache and the duplicated pilot-selector table

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 26
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration (iter-25) verdict was ESCALATE; mandatory, no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-01, J-08
- **Required-still-passing journeys:** J-02, J-03, J-04, J-05, J-06, J-09, J-10
- **Anti-goal reminders:**
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - Referee modules are byte-untouched this era — `referee_handoff_ready` never implies current-Referee registrability of a flow predicate; that awaits a future named revision of the referee spec. *(critical)*

## GOAL

Drive all nine stored journey-replay scripts through the deterministic replay lane in one recorded
machine run (closing a gap the evaluator has now flagged three rounds running), and fix the two
dev-owned, non-owner-blocked items the iter-25 evaluator named as safe to do now — the ~22s (growing
toward the ~13-minute-cold figure the evaluator measured against the real MCP tool) uncached
desk-readiness band-touch computation, and the duplicated Scout pilot-selector table in
`micro_routes.py` — with zero change to any served value.

## BACKGROUND

All 10 journeys read `passing` in `journey-history.json`, but the iter-25 evaluator (ESCALATE) wrote
in `iteration-state.md`'s Active blockers that the era is "NOT certifiable while 8 minor anti-goal
items stay open" and gave an explicit, ordered next-step list: (1) drive all nine stored checks in
one recorded run, including J-06's own; (2) fix the desk readiness cache; (3) collapse the duplicated
pilot-selector frozensets; (4) build the referee disclosure + guard; (5) [owner-owned, excluded — see
OUT OF SCOPE], with the evaluator's own instruction "if the clock bites, drop 4 and 5, never 1." This
iteration plans (1)-(3) and defers (4); it does not manufacture new journeys against a
"zero-FAILING-journeys" shortcut, because the evaluator's own most recent verdict is a live ESCALATE
naming concrete, non-owner-owned work — see the assumption ledger entry below for the full reasoning.

Depth is `full` because the prior verdict was ESCALATE (mandatory trigger 3, no exceptions) — not
because either code change independently warrants it (neither touches a persisted-schema migration
or an already-registered Data-Contract value's computing module/endpoint; both are purely additive
caching/dedup with byte-identical served values).

**Lesson applied (iter-25-second, lessons.md):** the deterministic replay lane is scoped to
Required-still-passing, which structurally excludes an iteration's own Target journeys — so a golden
a Target-journey iteration touches can never be machine-driven that same round. J-06's new Vault
golden hit exactly this three rounds running. This iteration's fix is structural, not another
one-off: neither J-01 nor J-08 (this round's Targets) carries a NEW golden assertion this round, and
the Required-still-passing list below is widened to the full remaining seven-golden set, so all nine
stored scripts (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09, J-10; J-07 has no golden by design,
per the iter-19 "Do not redo" ruling) run through the machine this iteration.

**Lesson applied (iter-21, lessons.md):** a new orchestration/entry-point function reachable only by
its own test is a defect the review/QA lanes have missed before. The new band-touch cache must be
reached by grepping its call site inside `joinable_corpus_counts`/`enumerate_band_touches` (the real
`GET /research/desk/micro/readiness` route path), not only by a new unit test — the reviewer/auditor
should re-run `grep -rn <new_cache_class> app/ tests/` and confirm at least one hit under `app/`.

## IN SCOPE

### Backend

- [ ] `micro_readiness.py` / `micro_join.py` / `micro_routes.py`: add a durable, per-`(dataset
  checksum, resolver.map_key(symbol, window_start_epoch))` SQLite cache for
  `enumerate_band_touches`'s per-dataset touch count, mirroring `MicroReadinessCache`'s existing
  `fallback_frac` table precedent (`micro_readiness.py:226-289`) — lookup-or-compute-and-publish
  inside `joinable_corpus_counts`, publishing ONLY a resolved count, never a "none"/placeholder
  value. Keying on the resolver's own `map_key` (not just the dataset checksum) means a re-warmed or
  changed band map is a genuine cache miss, never a stale hit under the old map. A corrupted/unreadable
  cache DB is a full miss, never a crash (the existing precedent's self-heal contract). `GET
  /research/desk/micro/readiness` and the `desk_micro_readiness` MCP proxy keep serving
  byte-identical values — only warm-path latency changes.
- [ ] `micro_routes.py`: derive `_BAND_TOUCH_PILOT_SELECTORS` / `_PLAYBOOK_SIGNAL_PILOT_SELECTORS`
  from `scout._PILOT_GRID_SELECTORS` (`scout.py:1684-1689`) by filtering on `kind`, instead of
  restating the two selector sets as a second hand-written literal — one canonical selector→kind
  source, per anti-goal rail 6 (single source of truth).
- [ ] Test-harness scope, not app code: widen this iteration's Required-still-passing set (below) to
  the full remaining seven-golden set so the deterministic replay lane drives all nine stored
  `journey-scripts/*.json` files in one recorded run this iteration, including `J-06.json`'s own
  Validation Vault assertion.

### Frontend

None — no frontend files change this iteration; served values and rendered UI are unchanged.

### New user-facing capability

None — this is backend performance and code-consolidation work.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible under normal operation; the `/desk` Microscope Readiness panel loads its band-touch
figure faster on a warm cache (previously ~22s uncached per dataset with a resolvable map, per the
iter-21 audit measurement; the same code path backs the `desk_micro_readiness` MCP tool's ~13.5s
warm / ~13min cold real-store timing the iter-25 evaluator log measured).

### Blueprint conformance

No new surfaces. The readiness value stays owned by `app/research/micro_readiness.py` (+
`micro_join.py`'s joinable-corpus contribution) and served by `GET
/research/desk/micro/readiness`, exactly the row already registered in `blueprint.md`'s Data
Contract — this iteration only makes an already-accepted caching pattern (the `fallback_frac`
precedent) durable for band-touch counts too. No `blueprint.md` edit is made this iteration.

### Data-contract additions

None — no new displayed value; `band_touch_count`'s shape and values are unchanged, only warm-path
latency. (No `blueprint.md` edit needed.)

## OUT OF SCOPE

- **Referee disclosure + guard/source-scan** for `strategy_trade_readiness`'s stale dataset/tick-gate
  count (owner ruling r5 point 7, "KEEP THE FREEZE, DISCLOSE" — anti-goal item open since iter-9).
  Deferred to a future iteration to avoid bundling two independently risky backend changes (a new
  cache-invalidation contract + work adjacent to the byte-frozen `referee_*` modules) in one diff;
  the iter-25 evaluator's own next-step ordering explicitly permits dropping this item under time
  pressure ("drop 4 and 5, never 1").
- **Chain-ledger identity-commitment gap** (`micro_chain_ledger.py:184-190`) — owner-owned per r8
  ("forbids designing it ad hoc"); its "minor" severity grounds expired at iter-23, but the FIX
  itself needs an owner ruling, not a dev-authored design. Not planned here.
- **Sealed judge's money-floor question** (`micro_sealed_evaluation.py`'s caller-supplied
  `econ_floor`) — owner-owned per prior rounds, blocks no journey, zero production callers.
- No real tape recording, no exposing or assigning any sealed shard, no running J-09's studies
  against the real recorded corpus (binding carry-forward from "Do not redo").
- The browser-QA-verdict-vs-closure-gate gap (`scripts/automation/lib/closure_gate.py`, anti-goal
  items tied to iter-21/24 lessons) — a pipeline/framework file outside this era's product scope;
  flagged for the human maintainer, not fixed inside this product iteration.
- No change to any `referee_*.py` module (byte-freeze holds) and no change to
  `micro_readiness.py`'s served response SHAPE — only an added internal cache layer.

## DEFINITION OF DONE

- [ ] Target journeys J-01, J-08 pass via browser-qa-agent (fresh evidence; served
  readiness/Scout-Ledger values unchanged post-cache/dedup) — TC-7, TC-8
- [ ] Required-still-passing journeys (J-02, J-03, J-04, J-05, J-06, J-09, J-10) remain green via
  deterministic replay of all nine stored goldens in one recorded run — TC-1
- [ ] No anti-goal violation introduced; rails 3/6/9 respected (frozen `referee_*` untouched, one
  canonical selector table, dataset checksums untouched) — TC-6, TC-9
- [ ] Unit tests pass; no regressions — TC-2, TC-3, TC-4, TC-5, TC-6
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-26-dev.md` — TC-10

## TESTING REQUIREMENTS

- Browser: J-01 "Microscope Readiness" section (fresh element screenshot, values byte-identical to
  pre-iteration); J-08 "Scout Ledger" section (fresh element screenshot, pilot-study family rows and
  `variants_tried` line unchanged).
- Unit/integration: new band-touch cache cold/warm/invalidation tests (co-located with the existing
  `MicroReadinessCache` tests); new selector-derivation equality + genuine-derivation guard tests
  (co-located with existing `test_scout.py`/`test_micro_routes.py` coverage); full backend suite run
  clean, zero regressions.
- Error cases: cache DB corrupted/unreadable → full miss, never a crash (TC-5); a dataset whose band
  map does not resolve still returns an honest `count: 0` / `not_enumerated`, never a fabricated
  cached value (existing behavior — regression-tested, unchanged).

Test-first contract:

- TC-1: given `journey-scripts/` holds nine stored goldens (J-01, J-02, J-03, J-04, J-05, J-06,
  J-08, J-09, J-10) and this iteration's Required-still-passing set is the full remaining seven,
  when the deterministic replay lane runs at iteration close, then
  `reports/phase-goal-rapid-microscope-iter-26-regression-replay-results.md` shows 9/9 PASS rows,
  including a PASS for `J-06.json`'s Validation Vault "Sealed at" assertion driven through the
  machine rather than resting on a dev-local claim.
- TC-2: given a dataset whose `(checksum, resolver.map_key(symbol, window_start_epoch))` pair has
  never been cached, when `GET /research/desk/micro/readiness` resolves that dataset's band touches
  for the first time, then the response's `joinable_corpus.band_touch_count.count` equals the
  hand-computed touch count for a committed fixture with a known band map, and the new cache table
  gains exactly one row for that composite key.
- TC-3: given that same `(checksum, map_key)` pair is now cached, when `GET
  /research/desk/micro/readiness` is called a second time, then `DatasetStore.load_events` is not
  invoked again for that dataset (asserted via a call-count spy) and `band_touch_count.count` is
  unchanged.
- TC-4: given a dataset's band map is re-warmed under a NEW `resolver.map_key` (a genuinely
  different tradability map version), when `GET /research/desk/micro/readiness` is called, then the
  cache records a miss under the new key and recomputes — the response never serves the OLD key's
  stale count under the new map identity.
- TC-5: given the cache DB file is corrupted or unreadable, when `GET
  /research/desk/micro/readiness` is called, then the request still returns HTTP 200 with a
  freshly-computed `band_touch_count`, never a 500 — mirroring `MicroReadinessCache`'s existing
  self-heal contract.
- TC-6: given `scout._PILOT_GRID_SELECTORS` is the one registered selector→(study, kind) table, when
  `micro_routes.py`'s `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` are derived
  from it by filtering on `kind`, then (a) a test asserts both derived frozensets equal today's
  known selector sets (`{RANGE_WALL_PILOT, DELTA_DIVERGENCE_PILOT}` /
  `{CAPITULATION_PILOT}`), (b) a second test extends a local copy of `scout._PILOT_GRID_SELECTORS`
  with a synthetic third `kind="band_touch"` entry and observes the route-level frozenset grow to
  include it — proving genuine derivation, not incidental equality — and (c) a source-scan/grep
  guard confirms `micro_routes.py` contains no second hand-written selector→kind literal.
- TC-7: given the `/desk` Microscope Readiness section is opened fresh after this iteration's cache
  change, when browser-qa-agent captures it, then the rendered totals/per-shard/floors values are
  byte-identical to the pre-iteration values (J-01's own registered acceptance figures), proving the
  caching change altered latency only, never a served value.
- TC-8: given the `/desk` Scout Ledger section is opened fresh after the selector-derivation change,
  when browser-qa-agent captures it, then the rendered pilot-study family rows and `variants tried`
  line are unchanged from the pre-iteration render, proving the dedup altered no classification
  outcome.
- TC-9: given every `referee_*.py` module and `micro_readiness.py`'s served response SCHEMA are
  frozen/registered surfaces this iteration must not mutate, when the reviewer/auditor re-hash
  `referee_*.py` against the iteration-0 SHA-256 listing and diff the readiness response schema,
  then all six referee hashes stay byte-identical and the readiness response schema is unchanged
  (the new cache is purely internal).
- TC-10: given the iteration completes, when the dev handoff is written, then
  `docs/handoffs/goal-rapid-microscope-iter-26-dev.md` exists and documents the cache's composite
  key design, the selector-derivation change, and the Required-still-passing widening rationale.

## NOTES

- **Target-journey selection is a deviation from the usual FAILING/PARTIAL rubric, stated per the
  pre-write self-check:** no journey is FAILING or PARTIAL this round. J-01 and J-08 are named as
  Target because they are the only two browser-verifiable journeys in this era whose owned surfaces
  this iteration's code touches (`docs/goal.md`: "J-01 and J-08 are browser-verifiable... the rest
  are keyless/automated with browser reveals landing in J-08"); J-04 (Scout, whose selector table is
  deduped) is itself keyless/automated and is covered instead by its own stored golden under
  Required-still-passing.
- The perf fix is expected to also relieve the `desk_micro_readiness` MCP tool's real-store timeout
  the iter-25 evaluator log measured (10s client timeout vs. ~13.5s warm / ~13min cold) — this is a
  welcome side-effect, not a graded DoD item, since the test suite stays keyless/hermetic per this
  era's own anti-goals and cannot assert against the operator's real store; the evaluator may spot-check
  it there directly.
- Blueprint (`state/blueprint.md`): no edit made this iteration — no new displayed value, no new
  page, no change to any already-registered module/endpoint pairing.
- Deferred item 4 (referee disclosure + guard) and the owner-owned items 5/29 remain open in
  `iteration-state.md`'s Active blockers; the evaluator should carry them forward unchanged, not
  re-derive their grounds again this round (nothing about their premises changed this iteration).

## Assumption ledger entry (also appended to `state/assumptions.md`)

See `runs/goal-session-rapid-microscope/state/assumptions.md`, entry `## iter-26 — goal-decomposer`.
