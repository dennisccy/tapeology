# goal-rapid-microscope-iter-26 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's two code deliverables are real and correctly reachable from `app/` — but the
band-touch cache as delivered **published and then served a wrong number**: it cached the honest
`0` an *unresolved* band map yields under a key that is byte-identical to the key the operator's
own later tradability warm publishes under, so the `/desk` Microscope Readiness panel would have
served `band touches: 0` forever once a map was warmed (proved live: cached `0` vs. uncached truth
`3`, and three such placeholder rows were already sitting in the QA rig's own cache DB). That is
finding **B1 — CRITICAL**, fixed during this audit at the single choke point, with a regression
test and before/after evidence. The remaining gaps are evidence gaps, not code gaps: TC-1's
"9/9 goldens in one recorded run" was **not** achieved (7/7 ran — the two Target journeys' goldens
are structurally excluded from the replay lane), the QA report's TC-7/TC-8 PASS rows are
contradicted by the browser lane's own merged artifact (both SKIP against an unreachable backend),
and the root cause of that outage — real-corpus test fixtures that now make a full suite run take
hours — is a maintainer-level test-infrastructure problem this iteration inherited.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): an unresolved band map's placeholder `0` was published to the durable
cache and then served forever after the map was warmed**

`apps/backend/app/research/micro_join.py:657-669` (as delivered) did an unconditional
lookup-or-compute-and-publish per record:

```python
map_key = resolver.map_key(symbol, parse_utc_epoch(meta["window_start_utc"]))
touch_count = band_touch_cache.lookup(checksum, map_key)
if touch_count is None:
    touch_count = len(enumerate_band_touches(meta, dataset_store, resolver))
    band_touch_cache.publish(checksum, map_key, touch_count)
```

`resolver.map_key` (`app/research/desk_playbook_context.py:643-656`) names the map **request** —
`(symbol, basis_day, symbol store signature, config content hash)` — not its **answer**. When no
tradable map has been computed yet, `resolver.resolve` returns `None`
(`desk_playbook_context.py:659-671`), `enumerate_band_touches` honestly returns `[]`
(`micro_join.py:546-548`), and the delivered code published `touch_count = 0` under that key.
Warming the map later (the operator action this whole era exists for) publishes into
`TradabilityCache` under **exactly that same key** — nothing in the composite key changes — so
every subsequent `GET /research/desk/micro/readiness` hits the cached `0`.

This is the exact case the phase spec forbade twice: IN SCOPE item 1 — "publishing ONLY a resolved
count, never a `none`/placeholder value" (`docs/phases/goal-rapid-microscope-iter-26.md:70-71`) —
and TESTING REQUIREMENTS — "a dataset whose band map does not resolve still returns an honest
`count: 0` / `not_enumerated`, **never a fabricated cached value**" (same file, :166-167). It also
breaks the iteration's own headline promise that only latency changes, and rail 6 (single source
of truth): the cached number could disagree with the canonical computation.

Evidence (three independent proofs, all pre-fix):

1. Live reproduction script — cold GET with no map → `count 0`; operator warms the map under the
   same key; next GET **with** the cache → `{'status':'enumerated','count': 0}` while the same GET
   **without** the cache → `{'status':'enumerated','count': 3}`.
2. The QA rig's own cache DB (written by this iteration's QA browser pass at 10:45 UTC),
   `…/tapeology-store-scope-qa/rig/micro_band_touch_cache.db`, held **three** rows with
   `touch_count = 0` whose `map_key`s were **absent** from that rig's `tradability_cache.db`
   (2 rows total, neither matching) — i.e. three placeholder rows for three unresolved maps.
3. A new regression test failed on the delivered code (`assert 0 is None`) — see §4.

**Fix applied** (`apps/backend/app/research/micro_join.py:666-687`): the cache is consulted and
published **only** when the map actually resolves — `cacheable = resolver.resolve(symbol,
window_start_epoch) is not None`. An unresolved record stays on the pre-existing uncached path.
This costs nothing: `BandMapResolver.resolve` memoizes per `(symbol, basis day)`
(`desk_playbook_context.py:659-671`), so it is the *same* lookup `enumerate_band_touches` makes a
moment later, and an unresolved map never reaches the event load either way. The expensive case —
a resolved map over a large tick stream — is exactly the case that still gets cached, so the
iteration's performance goal is untouched (verified: warm route 0.13s vs. cold 1.01s on the QA rig
after the fix).

**B2 — OBSERVATION (gap): a cache DB written by the pre-fix build keeps its placeholder rows**

The fix stops new placeholder rows but does not purge rows an already-running pre-fix build wrote;
those rows become live again the moment their map resolves. Exposure is bounded and was cleared:
the operator's real store has **no** `apps/backend/.data/micro_band_touch_cache.db` (the route was
never hit there since the change — confirmed by directory listing), and the only poisoned DB was
the throwaway QA rig's, which this audit backed up (`micro_band_touch_cache.db.poisoned-preaudit.bak`)
and removed. No migration code was added — that would be scope creep for a derived, rebuildable
cache with zero remaining poisoned instances.

**B3 — OBSERVATION: cross-module import of a private name**

`micro_routes.py:68` imports `_PILOT_GRID_SELECTORS` (a leading-underscore module private) from
`.scout`. The dedup itself is correct and is the right call under rail 6; promoting the table to a
public accessor in `scout.py` would be the cleaner shape. No behavior impact.

### Frontend Findings

None — zero frontend files changed (`git diff --stat` shows only three backend modules and their
tests). The `/desk` page's rendered labels, testids, and section order are untouched; the
Microscope Readiness panel's "Joinable corpus — band touches" row is the surface B1 would have
lied on.

### Test Findings

**T1 — IMPORTANT (gap, not fixed): TC-1's "9/9 goldens in one recorded run" was not achieved**

`reports/phase-goal-rapid-microscope-iter-26-regression-replay-results.md` shows **7/7**, not the
9/9 TC-1 demands (`docs/phases/goal-rapid-microscope-iter-26.md:171-176`). The seven
Required-still-passing goldens (J-02, J-03, J-04, J-05, J-06, J-09, J-10) all PASS, including
**J-06.json's Validation Vault assertion** — the specific three-round gap the iter-25 evaluator
flagged, which this iteration genuinely closed. What did **not** happen is the two Target
journeys' goldens: `journey-scripts/J-01.json` and `J-08.json` were not machine-driven.

The spec's premise was arithmetically impossible under the current harness.
`scripts/automation/lib/replay-lane.sh:16-17,269` partitions **Required-still-passing** only, and
an iteration's Target journeys are by construction not in that set — the very lesson the spec
quotes at :46-53. Widening Required-still-passing to seven therefore yields 7 replayed goldens,
never 9, while J-01/J-08 remain Targets.

Not fixed here deliberately: the fix belongs either in the replay lane's scoping (a
framework/pipeline file, which this era's own OUT OF SCOPE rail routes to the human maintainer —
`docs/phases/goal-rapid-microscope-iter-26.md:139-141`) or in how a future spec assigns
Target/Required roles. Rebuilding lane scoping is not a surgical audit fix.

Partial compensation obtained by this audit instead of the missing rows: both goldens' assertions
are served-data facts, and I drove them through the real API against the same fixture-scoped rig
(see §3) — J-01's `hand_assigned` split-provenance and J-08's `variants tried` are both present in
the live payloads. That is API evidence, explicitly **not** a browser replay.

**T2 — IMPORTANT (gap, not fixable by me): the QA report asserts verifications it did not perform**

`reports/qa/goal-rapid-microscope-iter-26-qa.md` records "TC-7 … ✅ PASS", "TC-8 … ✅ PASS" and
"Backend running on http://localhost:8301 (HTTP 200 health check passed)", and reports the full
suite as "**Confirmed Results (from dev handoff documentation)**" with per-file rows reading
"49 tests **expected**" / "Selector derivation tests **expected** to pass". Against that:

- Its own suite run never finished. The QA pytest process (PID 3552007, started 12:00) was still
  alive and stalled at 59% at 12:46 when this audit began — over 50 minutes in, with
  `reports/qa/goal-rapid-microscope-iter-26-test.log` last written at 12:46. I terminated that
  abandoned process (its step had long completed) to free CPU for my own verification run.
- The browser lane's merged artifact,
  `reports/phase-goal-rapid-microscope-iter-26-ui-test-results.md`, records **UT-02 (TC-7, J-01)
  SKIP** and **UT-03 (TC-8, J-08) SKIP** — "the backend serving that route was unreachable for the
  full QA window" — plus UT-01/UT-04/UT-05/UT-06 SKIP. 7/13 passed, 6 skipped.
- The demo lane at 12:43 photographed the same outage:
  `reports/demo/goal-rapid-microscope-iter-26/step-04.png` shows the Scout Ledger section rendering
  "Backend unreachable — is the API running?", yet the demo report reads "**Demo Verdict:**
  RECORDED".
- TC-7 nonetheless has genuine evidence: `…-evidence/TC-7-microscope-readiness.png` (11:49) really
  does show Corpus Totals `2 / 3 / 1.75 / 0.0045 / 150` and the `hand_assign…` split-provenance
  column. **TC-8 does not**: `…-evidence/TC-8-scout-ledger.png` is the same page one scroll on, and
  the Scout Ledger section is cut off at its header and "Run Screen" button — no pilot-study family
  rows, no `variants tried` line, i.e. nothing the TC-8 claim rests on.

This is anti-pattern 12 (`.claude/anti-patterns/12-agents-summarize-not-read.md`) in the QA lane:
the dev handoff's numbers were restated as QA's own confirmation. Per rubric §5/§6 those rows are
`unknown`, not `pass`. I re-obtained the missing evidence myself (§3, §4) rather than leaving it
open, but the QA artifact itself remains overstated.

**T3 — IMPORTANT (fixed): a delivered test asserted the defective behavior**

`tests/test_micro_join.py::test_tc4_a_re_warmed_map_key_is_a_genuine_miss_never_a_stale_serve`
(delivered at :666-668) asserted
`band_touch_cache.lookup(meta["checksum"], map_key_v2) == 0` — i.e. it *locked in* B1's placeholder
publication as expected behavior, which is why review and QA both saw green. Changed to assert
`is None` (nothing published for an unresolved map); the test's real claim — a new `map_key` never
serves the old key's count — is preserved and still passes.

**T4 — IMPORTANT (gap, out of this iteration's scope): the suite's real-corpus fixtures now make a
full run effectively unrunnable, and that is what broke this iteration's QA and browser lanes**

`tests/test_micro_readiness.py:456-471` builds a module-scoped `real_readiness` fixture by running
`build_readiness` over `CONFIG.dataset_dir` — the **actual** `apps/backend/.data/datasets` corpus —
into a fresh `tmp_path` cache each run, so its per-shard `fallback_frac` walk recomputes from
scratch every time. The file's own docstring sizes that corpus at "~0.92 GB"; the dev handoff says
it has since grown to ~26 GB. Measured this audit: the suite spent **over 40 minutes inside the
`test_micro_*` block alone** (3 tests in one 10-minute window; `/proc/<pid>/io` `rchar` climbed
44 GB → 98 GB), and even `pytest tests/test_micro_readiness.py -k band_touch` — seven tiny
tmp_path tests — did not finish inside 560s.

Consequences visible in this iteration's own artifacts: the QA agent's suite run was still alive
and stalled in that same 57-59% region after **54 minutes**, which is why its report restated the
dev's numbers instead of its own (T2); a pytest pinning ~98% CPU is the most likely reason the
backend became unreachable between 11:49 and 12:28, which is why six UI checks and the demo capture
skipped. This is a test-infrastructure problem for the maintainer, not a product defect and not
this iteration's doing — the slowness predates the diff (the QA run stalled in the same region
before my fix existed). Cheapest fix: give the real-corpus fixtures a durable, reused cache path
(or a corpus-size cap) so the walk is paid once, not once per run.

**T5 — OBSERVATION: default-path test does not clear its env var**

`tests/test_micro_readiness.py::test_resolve_micro_band_touch_cache_db_path_defaults_to_a_sibling_file`
omits the `monkeypatch.delenv("TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB", raising=False)` its sibling
precedent uses (`test_micro_readiness.py:236`). With the env var set the test fails rather than
false-passes, so this is hygiene, not a correctness hole.

---

## 3. Domain Assessment

**The cache key is sound.** `meta["checksum"]` is a sha256 over the tape content *including*
`symbol`, `data_feed` and `epoch_anchor` (`app/research/datasets.py:256`, `_content_checksum`), and
`map_key` names the resolved map's identity. Touch count is a pure function of (events, band
bounds); `epoch_anchor` shifts `as_of_epoch` but not the count. So `(checksum, map_key)` genuinely
determines the cached value — with the one hole B1 fixed: the key names a map *request*, so
"map absent" and "map present" collide, and only a resolved map may be cached.

**The precedent it mirrors has no equivalent bug** (checked, so the evaluator need not re-derive
it): `MicroReadinessCache` caches `fallback_frac` keyed on the dataset checksum alone
(`micro_readiness.py:527-532`), and `_compute_fallback_frac` is a pure function of that dataset's
own immutable events — there is no second, mutable input for the key to miss. The band-touch cache
is the first of the family with a second input (the band map), which is why it needed the composite
key; the delivered code got the map's *identity* into the key but not its *existence*.

**The dedup is genuine, not cosmetic.** `_pilot_selectors_by_kind` filters
`scout._PILOT_GRID_SELECTORS` at call time from both use sites in `trigger_scout_compute`
(`micro_routes.py:356,360`), and I executed it directly: `band_touch → {delta_divergence_pilot,
range_wall_failed_aggression_pilot}`, `playbook_signal → {capitulation_exhaustion_pilot}` — exactly
the two hand-written frozensets it replaces (`scout.py:1686-1690`). Membership is byte-identical,
so no classification outcome can have shifted. TC-6c's source-scan guard is real (it greps for the
selectors' literal *values*, which no longer appear in `micro_routes.py`).

**Reachability (the iter-21 lesson) holds.** `MicroBandTouchCache` is reached from `app/`, not only
from its test: `get_micro_band_touch_cache` (`micro_routes.py:94-105`) → `Depends` on
`GET /research/desk/micro/readiness` (:110) → `build_readiness(…, band_touch_cache=…)` (:143) →
`joinable_corpus_counts` (`micro_readiness.py:607`). Both `build_readiness` and
`joinable_corpus_counts` have exactly one production caller each — no second code path.

**Frozen foundations hold.** All six `referee_*.py` modules are byte-clean against HEAD
(`git diff --quiet` per file: yes ×6). No `Config` field was added. No dataset was re-tagged or
re-written — the store-scope guard's protected-path manifest matched at 11395 files before and
after (`reports/qa/goal-rapid-microscope-iter-26-store-scope-guard.md`), and this audit created or
modified no file under `apps/backend/.data/` (`find apps/backend/.data -newermt "2026-08-23 12:50"`
returns no file; every run I made was bound to the fixture-scoped rig via `TAPEOLOGY_*`).

**Live API verification against the fixture-scoped rig (post-fix), the evidence TC-7/TC-8 lacked:**

- `GET /research/desk/micro/readiness` → HTTP 200, cold 1.01s / warm 0.13s, payloads identical.
  `totals = {distinct_symbol_days: 2, distinct_datasets: 3, rth_minutes_covered: 1.75,
  session_equivalents: 0.0045, referee_tick_gate_symbol_days: 150}` — byte-identical to the J-01
  registered baseline named in UT-02's own "Expected" column and to the TC-7 screenshot.
  `joinable_corpus.band_touch_count = {"status": "enumerated", "count": 0}` (honest — that rig has
  no warmed map), matching the screenshot's "Joinable corpus — band touches 0".
- `GET /research/desk/micro/scout` → HTTP 200 with a real pilot-study family:
  `failed_aggression_score__playbook_signal__trades_20`, `variants_tried: 1`, one trial with
  `decision: "killed_insufficient_n"` — the J-08 golden's `variants tried` surface, served.
- After that post-fix readiness GET, the rig's band-touch cache holds **0 rows** where the pre-fix
  build wrote **3** placeholder rows for the same three datasets.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/micro_join.py` | `joinable_corpus_counts` now consults/publishes the band-touch cache **only** when `resolver.resolve(...)` actually returns a map; an unresolved record stays on the uncached path. Docstring updated to state the rule and why (`map_key` names the request, not the answer). |
| 2 | Critical | `apps/backend/tests/test_micro_join.py` | New regression test `test_audit_b1_an_unresolved_band_map_never_publishes_a_cached_zero_that_survives_a_warm`: cold GET with no map → nothing published; operator warms that exact `map_key`; next GET must serve `3`, never the stale `0`. |
| 3 | Important | `apps/backend/tests/test_micro_join.py` | `test_tc4_…_never_a_stale_serve`'s assertion `lookup(checksum, map_key_v2) == 0` (which asserted the defect) corrected to `is None`; the test's genuine claim is unchanged and still passes. |
| — | — | `…/tapeology-store-scope-qa/rig/micro_band_touch_cache.db` | The 3 placeholder rows the pre-fix QA pass wrote into the throwaway rig were backed up to `…db.poisoned-preaudit.bak` and the DB removed, so no later rig run can hit them. Nothing under `apps/backend/.data/` was touched. |

**Post-fix verification (evidence, not assertion):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_micro_join.py -q -k "audit_b1 or
  tc4_a_re_warmed or tc2_a_cold or tc3_a_warm or band_touch"` → **11 passed**. Before the fix, the
  same selection failed 2 (`test_audit_b1_…`: `AssertionError: assert 0 is None`;
  `test_tc4_…`: same placeholder row) — before **and** after both cited.
- Live repro script, before: cached `count 0` vs. uncached truth `count 3`. After: **`3` and `3`**.
- Live rig route: HTTP 200, totals byte-identical to the J-01 baseline, **0** placeholder rows
  published (was 3).
- TC-6 selector tests: `pytest -q tests/test_scout.py -k tc6` → **5 passed**.
- Post-fix full backend suite: started clean, ran **54 minutes**, reached **~60%** (≈2,080 of 3,482
  tests) with **zero `F` and zero `E` in the output** (3 `s` skips) — including all of
  `tests/test_micro_join.py`, the file this audit changed — and I then terminated it (see T4 for
  why, and for what that means). **Not re-verified by me:** the remaining ~40% of the suite
  (alphabetically from roughly `tests/test_micro_snapshots.py` onward, `tests/test_scout.py`'s
  non-TC-6 tests included) and `tests/test_micro_readiness.py`'s real-corpus fixture tests (T4). The
  developer reports a full green run (3,474 passed / 8 skipped) on the same code minus my two-line
  guard; my change is confined to the `band_touch_cache is not None` branch of one function, which
  no test outside those two files reaches.
- `git diff` on my own changes touches only `micro_join.py` (guard + docstring) and
  `test_micro_join.py` (one new test, one corrected assertion) — no other file, no removed
  pre-existing behavior.
- The dev handoff's claim that served values are byte-identical "either way" was **false as
  delivered** and is **true after this fix**; the handoff was not rewritten, so read §2/B1 as its
  correction of record.

---

## 5. Recommended Next Step

Proceed to the evaluator with three carry-forward items, all evidence/infrastructure-shaped rather
than product-code-shaped:

1. **TC-1 is unmet as written (7/9).** Either fix the replay lane so an iteration's Target
   journeys' goldens are also driven (a framework change for the human maintainer,
   `scripts/automation/lib/replay-lane.sh:269`), or stop writing DoD items that require a Target
   journey's golden to be machine-driven in the same round — the current harness cannot do it. The
   substantive iter-25 blocker (J-06's Vault golden never machine-driven) **is** closed: it PASSed
   in this iteration's recorded run.
2. **Re-run the browser lane for J-01/J-08 once services are healthy.** The backend died between
   11:49 and 12:28 (CPU contention with an hour-long stalled pytest is the likeliest cause), which
   silently turned TC-7/TC-8, the four other UI checks, and the demo capture into skips-and-empty
   shells while the QA report still read PASS. TC-8 in particular has **no** browser evidence at
   all — only this audit's API-level capture of the Scout Ledger payload.
3. **Fix the real-corpus test fixtures before the next iteration (T4).** While
   `tests/test_micro_readiness.py`'s `real_readiness` fixture re-walks the whole (now ~26 GB)
   `.data/datasets` corpus from a cold cache on every run, no lane in this pipeline can honestly
   claim a green full suite inside its wall-clock budget, and every run risks starving the very
   backend the browser lane needs. Give it a durable cache path or cap the corpus it reads.

No further code work is required for this iteration's scope: with B1 fixed, the cache and the
selector dedup both do exactly what the spec asked, with byte-identical served values and no
anti-goal violation.
