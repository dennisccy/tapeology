# goal-desk-iter-3 Audit Report

**Date:** 2026-07-25
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-03's goal is genuinely achieved: the screen store, row walker, compute manager, four routes and
CLI warmer exist, reuse the canonical owners verbatim, and were verified by me directly rather than
by trusting the handoff — `git diff` is empty on all 12 named frozen files, `Config().config_fingerprint()`
is `08e471b10130e1e2`, the full suite is **1299 passed / 8 skipped / 0 failed** (128s, exit 0), and
cross-process determinism (TC-10's literal clause, which no test actually covers) holds under two
different `PYTHONHASHSEED` values. One **IMPORTANT** defect was found by tracing the unhappy path
and is now fixed with two regression tests: `ScreenStore.record` silently **overwrote** a corrupted
snapshot file whose 5-pin key matched a re-run, erasing the integrity error the store had been
honestly surfacing — a direct breach of the critical anti-goal "snapshots are append-only … never
rewritten". The QA report also carried a fabricated TC-07 observation (a trigger "queue" that does
not exist), corrected in place. The remaining findings are documented GAPs, the most consequential
being that the "best band" rule ranks distance ahead of score, so AAPL's fixture row is summarized
by a score-57 band rather than the era's own pinned 300–302.4 wall — spec-conformant, but J-04 will
render it.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): a corrupted snapshot at the same 5-pin key was silently overwritten, erasing its integrity error**

`ScreenStore.record` (`apps/backend/app/research/desk_screen.py:449`) dedups by calling
`find_by_key` → `list()`, and `list()` (`:405-414`) *withholds* any file that fails its checksum,
routing it to `errors` instead. But the snapshot's path is a pure function of the same 5-pin key
(`screen_id = f"screen-{screen_date}-{checksum12}"`, `:458`), so on the corrupt-file path
`find_by_key` returns `None` while `write_text` (`:473`) lands on **that exact file** — a silent
in-place rewrite of a tampered snapshot.

Reproduced before the fix (probe, real `ScreenStore`, no mocks):

```
recorded id: screen-2026-06-22-ec5184e4966f
after tamper -> records: 0 integrity_errors: 1
find_by_key sees it: False
RE-RECORD SUCCEEDED -> id: screen-2026-06-22-ec5184e4966f
file bytes changed by the re-record: True
files on disk now: ['screen-2026-06-22-ec5184e4966f.json']
final -> records: 1 integrity_errors: 0        <-- the tamper signal is GONE
```

Two things fail here, both named as critical anti-goals: the snapshot is **rewritten** ("nothing is
silently … rewritten — a new run is a new snapshot"), and the honest integrity error the store was
surfacing **disappears** on the next routine re-trigger, so an operator investigating corruption
finds a pristine-looking file. It is also flatly contrary to the module's own claim that
"immutability is structural, not policed" (`:353`) and the dev handoff's "never a rewrite" claim.
The trigger requires out-of-band corruption first, which is why I rated it IMPORTANT rather than
CRITICAL — I was not fully certain of that boundary, since the damaged bytes are unrecoverably lost.

**Fix applied** — one guard at the single serialization choke point (`desk_screen.py:461-473`):
after the id is derived, if the target path already exists (which, given `find_by_key` found
nothing, can only mean that file failed verification), raise `ScreenIntegrityError` naming the file
and refusing to overwrite. `run_screen_and_record` catches only `ScreenAlreadyRecorded`, so this
propagates to `DeskScreenComputeManager._work` and resolves the job `"failed"` with the explicit
error — loud, never silent, never fabricated. Two regression tests added (see §4). Evidence:

```
$ .venv/bin/python -m pytest \
    "tests/test_desk_screen.py::test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite" \
    "tests/test_desk_screen_compute.py::test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite" -v
2 passed, 1 warning in 0.38s
```

**B2 — GAP: no already-recorded signal on the compute HTTP surface**

`docs/goal.md`'s J-03 step 3 asks for an "honest already-recorded response" on a same-pins re-run.
`run_screen_and_record` (`desk_screen_compute.py:107-113`) does return the existing snapshot, but
`_work` (`:187-196`) discards that return value, and the compute snapshot shape
(`:162-170`: `id/state/screen_date/started_utc/finished_utc/error/progress`) carries no `reused`
flag or recorded-snapshot id. So `POST`+`GET /research/desk/screen/compute` report an identical
`"done"` for a fresh compute and for a pure reuse; only the CLI hints at it, by printing the same
snapshot id twice (`:270-273`). Not a defect against the phase spec — its Data-contract addition #2
declares exactly the shape that shipped, and TC-4's literal clause ("the manager/store returns the
EXISTING snapshot (same `id`)") is met and tested — but J-04's "Run Screen" button cannot tell the
operator "nothing new was written". J-04 should either spec a deliberate contract addition
(`reused: bool` + `screen_id`) or diff snapshot ids/counts in the UI.

**B3 — GAP: an identical-pin retrigger always re-walks; the cheap pre-check is already available**

`DeskScreenComputeManager.trigger` never resolves the 5 pins before starting the walk, so a
re-trigger repeats every `compute_tradability` call (uncached — this path deliberately bypasses
`TradabilityCache`). The dev handoff logs this as a considered trade-off and the reasoning is sound
(row content is a pure function of the pins; the store refuses the duplicate structurally). Worth
recording that the pre-check is *already trivially available*: `compute_bar_store_signature`
(`desk_screen.py:185`) exists precisely to resolve the signature pin without the walk, and
`find_by_key` is public — yet `compute_bar_store_signature` currently has **no production caller**
(only `test_desk_screen.py:146/154/166`), so its stated purpose is unrealized.

**B4 — GAP: a compute with no universe registered persists a permanent empty snapshot**

`compute_screen` returns an honest empty walk when no universe exists (`desk_screen.py:278-280`) and
`run_screen_and_record` then **records** it (`universe_snapshot_id: null`, 0 rows, 0 skipped) —
pinned into an append-only, never-deletable store. Verified as intentional by
`test_desk_screen_compute.py:148-170`. It is honest, and a later real run for the same date pins a
different `universe_snapshot_id` so `latest`/`?date=` self-correct — but it diverges from this
iteration's own named precedent: the top-up CLI refuses with "no universe snapshot is registered --
nothing to top up" (`desk_topup_compute.py:351-354`) rather than recording an empty artifact.

**B5 — GAP: the meta-only list is lightweight on the wire only**

`get_screen` (`desk_routes.py:258-266`) calls `store.list()`, which parses **and sha256-verifies
every full snapshot** (`desk_screen.py:405-410`) before projecting to `_screen_meta_only`. The
payload shaping matches the spec's data contract exactly, but the stated rationale ("returning full
content for every historical snapshot … risks the era-5C latency mistake") is only half-addressed:
server-side work still scales with total snapshot bytes on every page-load GET. At ~100 rows/snapshot
this is tens of milliseconds, not the 5C 31.4s class of problem — but it is the same shape, and
`bars.py`/`datasets.py`'s stat-keyed-cache precedent exists for exactly this.

**B6 — OBSERVATION: the module docstring's "needs nothing from `routes.py`" claim is inaccurate**

`desk_screen_compute.py:13-19` states "**Unlike `DeskTopupComputeManager`, this manager needs
nothing from `routes.py`**", while `:52` is `from .routes import get_bar_index, get_bar_store,
get_dataset_store`. No import cycle results (`routes.py` does not import back), and the top-up CLI
imports the same resolvers, so this is prose drift rather than an architecture problem.

**B7 — OBSERVATION: a bare `assert` on a production path, and a `-> dict` annotation that returns `None`**

`run_screen_and_record` (`desk_screen_compute.py:112`) guards an invariant with `assert existing is
not None and existing["id"] == exc.existing_id`; if it ever fires, `str(AssertionError())` is `""`,
so the job would surface `state: "failed", error: ""` — a failure with no message. The same function
is annotated `-> dict` but returns `None` on the cancel path (`:96`).

**B8 — OBSERVATION: integrity errors from the universe/dataset stores are discarded during a walk**

`compute_screen` drops both error lists (`desk_screen.py:278`, `:286`). If the *newest* universe
snapshot file were corrupt, `records[-1]` silently becomes an older snapshot and the screen pins that
older id with no signal that a newer one is unreadable. Inherited verbatim from `desk_coverage.py:48`
(a zero-diff frozen file this iteration), and `GET /research/desk/universe` does surface the errors,
so the information exists on its owning endpoint.

**B9 — OBSERVATION: `coverage` / `bar_store_signature` describe whole-store freshness, not as-of state**

Both come from `get_desk_coverage`, whose `latest_window_end_utc` can post-date `screen_date`. This is
correct provenance (and TC-12 requires the byte-identical reuse), and no price value derives from it —
but J-04 must not render a coverage badge in a way that implies the screen consumed those bars.

**B10 — GAP (product consequence, spec-conformant): "best band" ranks distance ahead of score, so the
headline band is the nearest, not the strongest**

`_select_best_band` (`desk_screen.py:206-215`) implements the spec's tuple exactly
(`-class_rank, distance_bps, -quality_score`). Because distance is consulted before score, a
same-class band that happens to sit nearest the close always wins. Measured on the committed fixtures
(my probe, real `compute_screen`):

```
AAPL row      -> resistance, class C, distance 2.348 bps, band_score  57.0  (298.08–299.24)
AAPL's bands  -> resistance C score 123.0 at 300.23–302.25   <-- the era's own pinned wall, NOT selected
                 resistance C score  57.0 at 298.08–299.24   <-- selected (nearer)
MSFT row      -> resistance, class B, distance 413.8 bps, band_score 126.7 (395.10–397.83)
```

So the desk's one-line summary of AAPL is a score-57 band while the map's strongest same-class band
(score 123.0, the 300–302.4 wall era-5B pins as *the* tradable wall) is not the row's headline. This
is the logged decision in `assumptions.md` iter-3 entry 1 — whose own text notes goal.md states the
tuple for ordering the **final rows**, not for choosing a symbol's representative band — so it is not
a build defect and I did not change it. It is the single thing a human should look at before J-04
renders these rows, and before J-05's drill-in promises "the SAME 300–302.4 walls".

### Frontend Findings

None. `Frontend Present: no` is honest: zero frontend files touched, `git status` shows no
`apps/frontend/` entry, `UI_ROUTES`/`meta.py` carry zero diff, and the copy-discipline lint
(`tests/test_copy_discipline.py`, which walks the taxonomy payload plus frontend source literals) is
unmodified and green. No new desk copy exists to violate the descriptive-only rule.

### Test Findings

**T1 — IMPORTANT (fixed): the QA report recorded a fabricated TC-07 observation**

`reports/qa/goal-desk-iter-3-qa.md` TC-07 read "Second trigger while first running: **started=true**
(global single-flight queue) — Job merges into queue", contradicting both its own results table
("started:false on concurrent, same job … PASS") and the code (`desk_screen_compute.py:153-154`
returns `{"started": False, …}`). There is no queue: the second request is dropped. Verified at the
HTTP layer against the real routes with a deliberately slowed walk over the 103-member fixture
universe:

```
trigger#1                            -> 200  started = True
trigger#2 SAME date while running    -> 200  started = False   same job id = True
trigger#3 OTHER date while running   -> 200  started = False   screen_date served = 2026-06-22
poll -> running, members_total = 103 ; terminal -> done, members_done = 103
screens listed = 1 ; list entry has "rows" key = False ; counts = {'rows': 0, 'skipped': 103}
```

I rated this IMPORTANT (I weighed GAP) because it is a *fabricated mechanism*, not a loose wording,
and QA reports are the evidence base the goal-evaluator and the next decomposer build on — J-04's UI
would have been designed against a queue that does not exist. **Fixed**: the block is corrected in
place with the evidence above and marked as an audit correction; the PASS verdict is unaffected,
since the implemented behavior matches the phase spec's TC-7 and the handoff's global-single-flight
reading.

**T2 — GAP: TC-10's "two separate fresh test processes" is not what the test does**

`test_repeat_computation_in_two_fresh_instances_is_byte_identical` (`test_desk_screen.py:553`) uses
fresh store *instances* inside one process; the QA table nonetheless claims "Two processes produce
identical rows … Verified in test_second_run_with_identical_pins". I supplied the missing proof
myself — the same computation in two separate interpreters under different hash seeds:

```
PYTHONHASHSEED=0      rows=2 skipped=101 sig=6a492196f697672e digest=7fa86050cba72753...12109e39
PYTHONHASHSEED=12345  rows=2 skipped=101 sig=6a492196f697672e digest=7fa86050cba72753...12109e39
```

The behavior is correct; only the test net is narrower than the TC text. Not fixed (a subprocess
test is infrastructure the correctness does not need).

**T3 — GAP: the new route tests read the ambient `.data/datasets` tree**

`route_ctx` (`test_desk_screen_compute.py:368-371`) scopes `TAPEOLOGY_DESK_UNIVERSE_DIR`,
`TAPEOLOGY_BAR_DIR` and `TAPEOLOGY_DESK_SCREEN_DIR` but **not** `TAPEOLOGY_DATASET_DIR`, and
`trigger_desk_screen_compute` resolves `get_dataset_store()` — so those tests walk the operator's
real dataset store (`config.py:1330-1335` falls back to the package default). No assertion depends on
it, so the tests are stable, and no network is touched (the keyless/hermetic anti-goal is not
literally breached), but it violates the iter-1/iter-2 rule "never read the ambient `.data/` tree
from a test". The dev's own CLI fixture shows the seam is understood (`_set_cli_env`, `:504`, sets it).
One-line remedy for a later iteration.

**T4 — OBSERVATION: two loose assertions in otherwise tight tests**

TC-1 asserts `row["distance_bps"] == pytest.approx(expected_distance)`
(`test_desk_screen.py:509`) where the spec's word is "byte-identical" and the test recomputes the
identical expression, so exact equality is achievable. TC-2 includes a vacuous
`assert row["band_class"] in ("A","B","C",None)` (`:529`) — always true; TC-14 is what actually pins
MSFT to class B.

**T5 — OBSERVATION: TC-8's "fewer than members_total" holds only under the fake's timing**

`compute_screen` checks `should_abort` *before* each member and reports progress *after* it
(`desk_screen.py:294`, `:327`), so a cancel arriving after the final member yields
`state: "cancelled"` with `members_done == members_total` and a fully-completed walk thrown away
unrecorded. Honest, and the outcome is safe — just not the shape TC-8's wording implies.

---

## 3. Domain Assessment

The core domain logic is correct and, unusually, *provably* reusing its owners rather than
re-deriving them. Three things I specifically tried to break and could not:

- **Single source of truth.** `compute_screen` calls `compute_tradability` directly, not through
  `TradabilityCache` — which sounded like a divergence risk until I checked the cache key: one row
  per "(symbol, basis session, store content, config content)" (`tradability_cache.py:143`), so a
  stale entry cannot make the route disagree with the screen. TC-1 then proves it the strong way,
  cross-checking the row against the **real** `GET /research/tradability` through `TestClient`, not a
  module call. `coverage` is `get_desk_coverage`'s own per-member block byte-for-byte (TC-12).
- **No lookahead.** `as_of = f"{screen_date}T23:59:59Z"` is a pure function of the operator's date
  (`desk_screen.py:163-166`); `_resolve_basis` admits only bars whose UTC session date is *strictly*
  before it, and the reference close is that same basis bar's own close — the identical
  `current_price` `compute_tradability` used for its side split, so the distance and the side split
  can never disagree. The `_iso`-string comparison on both sides (`:227-245`) correctly avoids an
  epoch round-trip.
- **A resolved basis with zero bands** would crash `min()` in `_select_best_band`. It is genuinely
  unreachable: the prior session's own close is always a level and sorts to the support side
  (`tradability.py:429`), so at least one band always exists once a basis resolves — the frozen
  module documents exactly this at `:86-88`.

Skip reasons are honestly distinct, with one nuance worth naming: a symbol holding intraday bars but
no `1d` series takes `compute_tradability`'s second empty branch (`tradability.py:388-392`) and is
labeled `"no_basis"`. That is the more honest of the two permitted labels — `"no_bars"` would be a
lie when bars exist — and the row's `coverage` disambiguates per timeframe. `bar_store_signature` is
structurally incapable of a `BarStore` read (it receives no store), which is a better guarantee than
the instrumentation TC-15 asks for; note though that TC-15's test exercises
`compute_bar_store_signature`, which nothing in production calls (B3) — the production path is
index-only for the same structural reason, which I confirmed by reading it.

Scope discipline is genuinely clean: zero new `Config` field, `git diff` empty on all 12 frozen
owners, and the only removed lines in `desk_routes.py` are docstring text plus one import line that
was widened — every pre-existing handler body is byte-unchanged, which I verified from the diff
rather than from the handoff's assertion. The new MSFT fixtures are real vendor data, not the
synthetic stand-in `lessons.md` iter-2 warns about: float32 round-trip artifacts
(`470.84320068359375`), real volumes, 120 daily bars, matching the AAPL fixture's shape exactly.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/desk_screen.py` | `ScreenStore.record`: refuse with `ScreenIntegrityError` when the 5-pin key's own deterministic path already holds a file that failed verification, instead of silently overwriting it and erasing the surfaced integrity error (B1). One guard + one docstring sentence; no other behavior touched. |
| 2 | Important | `apps/backend/tests/test_desk_screen.py` | Regression test `test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite`: asserts the raise, the damaged file's bytes are unchanged, `integrity_errors` still names it, and no second file appears. Also imports `ScreenIntegrityError`. |
| 3 | Important | `apps/backend/tests/test_desk_screen_compute.py` | Regression test `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`: the job-level view — a re-trigger onto a corrupted snapshot resolves `"failed"` with the integrity error, bytes unchanged, nothing recorded. |
| 4 | Important | `reports/qa/goal-desk-iter-3-qa.md` | Corrected the fabricated TC-07 narrative (a trigger "queue" that does not exist) with the real HTTP-layer evidence, marked as an audit correction (T1). |

**Post-fix verification** (all commands run with the pipeline's isolated `TMPDIR`):

- Targeted: the two new regression tests — `2 passed in 0.38s`.
- Desk + guard subset: `pytest tests/test_desk_screen.py tests/test_desk_screen_compute.py
  tests/test_desk_universe.py tests/test_desk_coverage.py tests/test_desk_topup_compute.py
  tests/test_no_execution_path.py tests/test_no_credential_in_artifacts.py -q` — all green.
- Full suite: `pytest tests/ -v` → **`1299 passed, 8 skipped, 2 warnings in 128.10s`**, exit 0
  (dev/QA's 1297 + my 2 regressions; iter-2 floor 1240/8 held, zero regressions).
- Pins re-verified after the fix: `Config().config_fingerprint()` = `08e471b10130e1e2` (fresh
  instance and singleton); `git diff HEAD` numstat = 0 lines on `config.py`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `desk_universe.py`, `desk_coverage.py`,
  `desk_topup_compute.py`, `routes.py`, `main.py`, `meta.py`, `mcp/__init__.py`.
- Diff self-review: my change to `desk_screen.py` is one guard block plus one docstring sentence
  inside `record`, and nothing else in the file or the repo changed. No escape hatch and no
  silenced error was introduced — the fix converts a silent overwrite into an explicit, honest
  failure. The dev handoff's claims are not invalidated by it; its "never a rewrite" claim is now
  actually enforced rather than merely asserted.

---

## 5. Recommended Next Step

**Proceed to J-04 (the `/desk` page).** J-03 ships the capability the page needs, and every DoD item
was independently verified, not accepted on report. Carry three things into J-04's spec:

1. **Decide what the row's headline band should be (B10).** J-04 renders `band_class`/`distance_bps`/
   `band_score` as the operator's one-line read of a symbol; today distance-before-score makes
   AAPL's headline a score-57 band while the era's own pinned 300–302.4 wall (score 123.0) sits
   unmentioned in the row. Either accept it explicitly in the UI copy ("nearest same-class band") or
   respec the within-symbol selection tuple — a human call, not a build fix.
2. **Give the compute surface an honest reuse signal (B2)**, as a deliberate data-contract addition
   (`reused: bool` + the recorded `screen_id`) so the "Run Screen" button can say "reused the
   existing snapshot" instead of an indistinguishable "done".
3. **Two one-line hygiene items** while `/desk` work touches these files: scope
   `TAPEOLOGY_DATASET_DIR` in `route_ctx` (T3), and refuse-rather-than-record a screen when no
   universe is registered (B4), matching the top-up CLI's own precedent.

Nothing here blocks J-06 (the MCP `desk_screen` tool), which J-03 now unblocks as intended.
