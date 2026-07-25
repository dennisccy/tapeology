# goal-desk-iter-2 Audit Report

**Date:** 2026-07-25
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-02 is genuinely built, not claimed: I independently re-ran the suite (**1240 passed / 8 skipped / 0
failed**, exit 0, counted from the progress stream — floor 1210/8), re-printed the pin
(`08e471b10130e1e2`), and — because the delivered tests prove the top-up only against `FakeAdapter`
— drove the shipped CLI warmer **four times against the real keyless Yahoo vendor** in temp-scoped
dirs: no-universe → honest stderr + exit 1; a bogus ticker → 4 honest `failed` outcomes with the
vendor detail preserved verbatim + exit 1 (run continued past each failure); AAPL → `4 fetched`
(exit 0) then, re-run the same UTC day, **`4 reused` (exit 0)** — store-first proven at the operator's
real surface, through the real retention clamp the fixtures cannot exercise. Coverage at real scale
(101-member snapshot × 4 timeframes = 404 index queries) reads in **1.5 ms** with zero `BarStore`
calls, and the real `.data/` tree was untouched by every test and probe.

Four documented GAPs remain, none of which compromises the phase goal: the top-up labels the frozen
route's "identical content already on file" 409 as `"failed"` (reachable on a weekend/holiday re-run,
~100 `1w` pairs); `latest_window_end_utc` is the *requested* window end, not the last actual bar
(real AAPL `1w`: window_end `2026-07-25`, covered_end `2026-07-20`); the CLI warmer — whose cited
precedent has 10+ `main()` tests — has zero automated coverage; and the route-level coverage payload
is only unit-tested in its empty state. All four are documented below rather than fixed: each fix
would either breach a critical anti-goal (frozen `POST /research/bars` behaviour), blur the
store-first evidence semantics the DoD relies on, or is scope creep per this role's rules.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented; considered IMPORTANT, see reasoning): a benign "content already on file"
refusal is reported as `outcome: "failed"`, and the CLI exits 1**

`desk_topup_compute.py:146-147` maps every `HTTPException` from `record_bar_series` to
`("failed", detail)`. One of those is not a failure: `routes.py:680-691` raises **409** when the
vendor returns content byte-identical to a series already on file *and* `stale_clamped is None`
(the normal case) — i.e. "nothing new to record", not "the pair could not be topped up".

Reproduced directly (auditor probe, `POST /research/desk/topup/compute` through the app, window
strings shifted to the next UTC day while the vendor returned identical content):

```
--- next-UTC-day re-run, identical vendor content ---
state: done
outcome mix: {'failed': 12}
new vendor calls: 12
   AAA 1h failed | this exact bar series is already registered as 'c500ff87…' (AAA 1h)
                 — bar series are immutable and are never re-recorded
```

Realistic trigger: the top-up's window is `[today-730, today]` (`desk_topup_compute.py:91-101`), so
a re-run on a **later** UTC day always re-fetches. `1w` rows change only while the market trades, so
a Fri→Sat or Sat→Sun re-run returns byte-identical weekly rows for most symbols → for a 101-member
universe, ~100 `1w` pairs report `"failed"`, ~100 real vendor calls are burned, and
`main()` (`desk_topup_compute.py:372`) exits 1 with nothing actually wrong. Coverage itself stays
correct throughout (verified: `coverage AAA 1d after re-run: {"has_bars": true, …}`).

Why GAP and not IMPORTANT (I was genuinely unsure): the outcome is **honest and non-silent** (the
frozen owner's detail is preserved verbatim), the walk continues, `has_bars` never regresses, and the
behaviour conforms to the registered Data-Contract vocabulary `{reused, fetched, failed}`. Why I did
NOT fix it: (a) collapsing 409 → `"reused"` would destroy the meaning the DoD leans on — `"reused"`
currently implies *zero vendor calls* (TC-7's store-first proof); (b) `routes.py:691`'s 409 is a
frozen kept-surface behaviour explicitly pinned by `tests/test_bars_api.py:8` ("re-recording
DIFFERENT-window-but-identical CONTENT is 409"), so touching it breaches the *Frozen foundations*
critical anti-goal; (c) a fourth outcome value (`"unchanged"`) is a Data-Contract/blueprint change,
which is a spec author's call, not an auditor's. **Route this to J-03/J-04's spec**: the desk UI must
not render this as a red failure wall.

**B2 — GAP (documented): `latest_window_end_utc` is the REQUESTED window end, so the coverage
"freshness" field reads fresher than the data actually is**

`bar_index.py:154-176` returns `MAX(window_end_utc)`, and `desk_coverage.py:58-62` serves it as
`latest_window_end_utc`. `window_end_utc` is the verbatim *request* string (`routes.py:675-676`),
not the last bar. Real recordings made today by the shipped CLI:

| tf | `window_end_utc` (served as freshness) | `covered_end_utc` (last real bar) | `vendor_limit` |
|----|----------------------------------------|-----------------------------------|----------------|
| 1w | 2026-07-25T00:00:00Z | 2026-07-20T04:00:00Z | none |
| 1d | 2026-07-25T00:00:00Z | 2026-07-24T04:00:00Z | none |
| 4h | 2026-07-25T00:00:00Z | 2026-07-24T17:30:00Z | SET |
| 1h | 2026-07-25T00:00:00Z | 2026-07-24T19:30:00Z | SET |

`BarIndex.coverage("AAPL", tf)` reported `2026-07-25T00:00:00Z` for all four — 5 days fresher than
the real `1w` data, and for a halted/delisted symbol with only old bars it would read as today-fresh
indefinitely. This is **spec-conformant, not a defect**: TC-4 and the blueprint Data-Contract row
both define the field as the raw `bar_index` column, and `covered_end_utc` is not in `_SCHEMA`
(`bar_index.py:44-56`) — adding it is an explicitly OUT OF SCOPE schema change. Recorded because the
blueprint row is titled "coverage **+ freshness**" and J-04 will badge it: J-04 must label it
"window last requested", never "last bar", or read `covered_end_utc` from the store for the few rows
it renders.

**B3 — OBSERVATION: "latest universe snapshot" is re-selected in four places**

`records[-1]` appears at `desk_routes.py:127` (J-01, pre-existing), `desk_coverage.py:53`,
`desk_topup_compute.py:231`, and `desk_topup_compute.py:358`. All four read the one canonical
`UniverseStore.list()` (correctly sorted by `created_utc`, `desk_universe.py:378`), so no divergent
value can be served — I verified empirically that `/research/desk/universe` and
`/research/desk/coverage` agree on the same `universe_snapshot_id` over the real 101-member snapshot.
A `UniverseStore.latest()` accessor would collapse the four; adding it now is scope creep.

**B4 — OBSERVATION: the `stale_clamped` 409-recovery mislabel (reviewer NOTE) is unreachable from
the top-up**

`desk_topup_compute.py:151-155` classifies by `created_utc`, so `routes.py:687-688`'s recovery return
would read `"reused"` after a real vendor call. Verified narrower than the review states: that branch
needs a *byte-identical window key* recorded on an earlier UTC day, and `_fetch_window_now()`
re-keys every calendar day — so the top-up itself can never produce it. Only a hand-crafted
`POST /research/bars` sequence can. Correctly telemetry-only.

**B5 — OBSERVATION: `_TOPUP_LOOKBACK_DAYS = 730` always trips Yahoo's own 1h/4h retention clamp**

`desk_topup_compute.py:80` asks for exactly 730 days from `00:00Z`, while
`yahoo.py:_clamp_to_retention` measures its horizon from `now` — so the start is always clamped and
**every real 1h/4h recording carries a non-null `vendor_limit`** (table in B2; the note is surfaced
verbatim in the failure detail I captured: "…so the requested start was moved forward to
2024-07-25"). Honest (the adapter states the shortfall) and harmless today, because
`_clamped_window_may_have_grown` (`routes.py:499-516`) only bypasses store-first on a *later* UTC
day, where the window key has already changed. Recorded so a future iteration that pins a fixed
window knows those series are permanently flagged clamped.

**B6 — OBSERVATION: a misplaced section banner** — `bar_index.py:150` (`# --- list (the GET filter)`)
now sits directly above the new `coverage()` method at `:154`, so it labels the wrong function.
Cosmetic.

**B7 — OBSERVATION: a killed process can leave one corrupt bar file (inherited)** — the worker is
`daemon=True` (`desk_topup_compute.py:276`) and `main.py`'s shutdown drain does not join it (dev
disclosed this), while `BarStore.record` writes non-atomically (`bars.py:575`, no temp+rename). A
restart mid-write leaves a truncated JSON that every reader surfaces in `integrity_errors` and never
serves as data, that `bar_index` never learned of (insert happens after record, `routes.py:696`), and
that a re-run heals by recording a new immutable series. Inherited from a frozen owner
(`bars.py` is OUT OF SCOPE); flagged because J-03's screen snapshots will write on the same pattern.

### Frontend Findings

**None — correctly zero frontend surface.** `Frontend Present: no` is honest: `git status` shows no
frontend file touched, `UI_ROUTES` is still exactly 2 rows (`['/', '/structure']`, verified live),
and the three UI-chain reports all say N/A consistently. J-02's badges are J-04's job per
`blueprint.md`'s journey-homes table.

### Test Findings

**T1 — GAP (documented): the CLI warmer has zero automated tests, unlike the precedent it mirrors**

`desk_topup_compute.py:329-372` (`main()`) is a named IN SCOPE deliverable. No test references it
(`grep -c main` over the new test files: 0), while the precedent the spec told it to mirror,
`edge_report_compute.main()`, has 10+ direct tests (`tests/test_edge_report_compute.py:442,470,485,
496,510,519,541,561,583,624`). Its uncovered logic is real: the no-universe guard, member resolution,
the summary counters, and the exit-code mapping. **I closed the evidence hole myself** rather than
leave it `unknown` — four real runs, temp-scoped (`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR`/
`TAPEOLOGY_BAR_INDEX_DB`), real keyless Yahoo, `.data/bars` file count 128 → 128 unchanged:

```
# no universe registered
no universe snapshot is registered -- nothing to top up (run POST /research/desk/universe/fetch first)   exit=1
# bogus ticker (real vendor)
[ZZZZNOTAREALTICKER 1h] failed -- no data for … — Yahoo Finance serves 1h bars only for the last 730 days…
[ZZZZNOTAREALTICKER 4h] failed …   [ZZZZNOTAREALTICKER 1d] failed …   [ZZZZNOTAREALTICKER 1w] failed …
desk top-up complete: 0 fetched, 0 reused, 4 failed.                                                     exit=1
# AAPL, real vendor, first run
[AAPL 1h] fetched  [AAPL 4h] fetched  [AAPL 1d] fetched  [AAPL 1w] fetched
desk top-up complete: 4 fetched, 0 reused, 0 failed.                                                     exit=0
# AAPL, same UTC day, second run  -> store-first at the REAL surface
[AAPL 1h] reused   [AAPL 4h] reused   [AAPL 1d] reused   [AAPL 1w] reused
desk top-up complete: 0 fetched, 4 reused, 0 failed.                                                     exit=0
```

The deliverable works end-to-end; only the regression net is missing. Not fixed (adding tests is
GAP-level work per this role's rules) — a future iteration should add the three cheap `main()` cases.

**T2 — GAP (documented): the route-level coverage payload is tested only in its empty state**

`tests/test_desk_topup_compute.py:459-471` asserts the honest-empty route body; the populated
truth-table is asserted only against the function directly
(`tests/test_desk_coverage.py:108-125`) — no test drives `GET /research/desk/coverage` with bars
present, so the route's dependency wiring (`get_bar_index` vs the store the top-up wrote to) is
unproven by the suite. Closed by hand (auditor probe, route-level, after a real
`POST /research/desk/topup/compute`): HTTP 200, 3/3 members, all four timeframes
`has_bars: true`, and at real scale 101/101 members with `universe_snapshot_id` matching
`GET /research/desk/universe`.

**T3 — GAP (documented): TC-8's literal cancel-then-resume is decomposed, never exercised as one
flow.** `tests/test_desk_topup_compute.py:330-370` pre-records M pairs instead of cancelling a real
run, and the cancel-mechanics test (`:194-228`) uses a fake `_run_one_pair` that records nothing. The
test's own docstring is honest about this, and the risk it would catch is small (cancel is observed
*between* pairs, `desk_topup_compute.py:181-182`, so the store is never left mid-write). Both halves
of the guarantee are separately proven; the composite is not.

**T4 — GAP (documented): goal.md's literal J-02 acceptance symbols are not what the truth-table
asserts.** `docs/goal.md:359-361` says coverage must report bars-present "for exactly the members the
era-open store holds (AAPL/AMD/MSFT)" over *the fixture universe*. The delivered truth-table uses
synthetic `AAA…EEE` with 2 of 5 covered (`tests/test_desk_coverage.py:18-19,108-125`); the committed
fixture universe is not referenced by either new test file, and `AAPL|AMD|MSFT` appears 0 times. This
matches the iteration spec's own TC-3 **verbatim**, and is hermetically better (the spec's NOTES
forbid touching the ambient real dir where AAPL/AMD/MSFT bars live). Substance delivered, letter not
— recorded so the goal-evaluator judges on facts.

**T5 — OBSERVATION: the widened kept-route capture is 24 of 27 kept GET templates.**
`runs/goal-desk-iter-2/kept-route-{baseline,after}-24.txt` are byte-identical (verified: `diff` →
empty) and cover 24 rows against a genuinely populated dir (`/research/bars` 37,274 B,
`/research/levels` 30,724 B — exactly the class iter-1's near-empty capture could not exercise, audit
T2 discharged). Enumerating the live OpenAPI shows **27** non-desk GET templates; the three unprobed
are `/health`, `/market/clock`, `/symbols/search` — the latter two are vendor-backed and
wall-clock-dependent, so they could never be byte-stable. "All 24" is the spec's own count, not all
kept GETs.

**T6 — OBSERVATION: test-count reporting is inaccurate in two artifacts.**
`docs/handoffs/goal-desk-iter-2-dev.md:74-75` says "41 new tests … plus 5 additive";
`reports/qa/goal-desk-iter-2-qa.md:39` says "Total new tests: 40". The true delta is **+30**
(8 + 17 + 5), matching 1210 → 1240 exactly; the handoff's own "Tests Run" section states +30
correctly. 40 is the *total* in those three files (10 pre-existing `test_bar_index.py` tests
included).

---

## 3. Domain Assessment

The core domain decisions are right, and the honesty discipline holds where it matters.

**Coverage is genuinely index-only, and fast at real scale.** `desk_coverage.get_desk_coverage`
(`desk_coverage.py:39-69`) is structurally incapable of reaching a `BarStore` — it is never handed
one — and `BarIndex.coverage` (`bar_index.py:170-176`) is a single `COUNT`+`MAX` whose `WHERE
symbol=? AND timeframe=?` is the leftmost prefix of the table's primary key, so SQLite serves it from
the implicit PK index. Measured, not assumed: 101 members × 4 timeframes over 1,212 indexed rows =
**1.5 ms** (best of 5), 34 KB payload. T-4 (the era-5C 31.4 s re-hash mistake) is genuinely closed,
and the class-level `BarStore.list`/`.get` call-counting guard (`tests/test_desk_coverage.py:162-191`)
will catch a future fallback.

**The `bar_index` extension really is additive.** The dev rejected the plan's other option (a new
`BarIndexHit` field) for a correct reason I verified: `tests/test_bar_index.py` compares whole
`BarIndexHit` instances built with exactly three positional fields, so a defaulted fourth field
would have silently passed until a real `window_end_utc` diverged. `git diff --numstat`:
`bar_index.py` **+26/-0**, `test_bar_index.py` **+67/-0** — no existing line touched, `_SCHEMA`
untouched, `.lookup()`/`.insert()`/`.list()`/`.reindex()` untouched, and the new dataclass-shape pin
(`test_bar_index.py:236-245`) makes the constraint explicit for the future.

**Reuse over reimplementation is real, not claimed.** `_run_one_pair` (`desk_topup_compute.py:141-155`)
calls `routes.record_bar_series` in-process; `routes.py` has **zero diff**, as do `main.py` and
`config.py`. There is no second fetch-and-record path, no second coverage index, no new `Config`
field, and therefore no fingerprint movement (`08e471b10130e1e2`, re-printed live). Resumability is
correctly *delegated* to the store-first coordinator rather than reinvented as checkpoint
bookkeeping — the leanest correct design, and the one whose failure mode (a shorter `outcomes` list)
is honest by construction.

**The compute manager's concurrency is sound.** The single-flight test-and-publish happens under one
lock (`desk_topup_compute.py:225-245`), `_publish`/`_resolve` both re-check job identity before
touching state (`:250`, `:285`) so a superseded job can never overwrite a newer one, the snapshot is
rebound in a single assignment and deep-copied for readers (`:108-116`, proven by the poison test at
`tests/test_desk_topup_compute.py:255-272`), and a cancel that lands before the thread starts is
still observed. Cancellation is cooperative and checked *between* pairs, never mid-record. The one
disclosed deviation — a module-level singleton behind a FastAPI dependency instead of a
`ResearchRegistry` property — is forced by a genuine import cycle (`desk_topup_compute` must import
`routes`), is documented in three places, and costs only the shutdown join of a daemon thread whose
"in-flight jobs honestly lost on restart" contract every compute manager here already carries.

**Honest failure handling is the strongest part.** Per-pair exceptions are caught, labelled
`"failed"` with the detail preserved verbatim, and the walk continues — proven in the suite with a
purpose-built adapter that fails exactly one of eight calls (so "continues" is distinguishable from
"stopped"), and proven again by me against the real vendor, where all four pairs of a bogus ticker
reported the vendor's own retention/no-data sentences. A catastrophic failure outside any pair
resolves the whole job `"failed"` with the message intact. `GET`-never-computes holds on both new
GETs (both are pure reads; asserted with a vendor call-counter). Hermeticity holds: the three new
test files pass in 3.3 s with the real `.data/{bars,universe,bar_index.db}` mtimes byte-for-byte
unchanged before and after.

The residual weakness is semantic, not structural: the `{reused, fetched, failed}` vocabulary is
inferred from a `created_utc` comparison and cannot express "the store already holds exactly this
content" (B1) or distinguish "asked through today" from "has bars through today" (B2). Both are
contract-level choices the spec made deliberately, both are honest at the payload level today, and
both become *visible* the moment J-04 renders them — which is where they should be resolved.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** No CRITICAL or IMPORTANT finding survived verification, so no source file was modified. Every finding above is GAP or OBSERVATION, which this role documents rather than fixes; B1's only in-scope "fix" would breach the *Frozen foundations* critical anti-goal (`routes.py:691`'s 409 is pinned by `tests/test_bars_api.py:8`) or blur the store-first evidence semantics the DoD depends on. `git status` shows the working tree carries only the developer's diff. |

**Verification performed instead of fixes** (all commands run with the isolated `TMPDIR`):

| Check | Command | Result |
|---|---|---|
| Full suite | `.venv/bin/python -m pytest tests/ -q` | exit 0; **1240 passed / 8 skipped / 0 failed** (counted from the progress stream — the repo's `addopts = "-q"` plus a second `-q` suppresses the summary line) |
| Pin | `Config().config_fingerprint()` | `08e471b10130e1e2` unchanged |
| New tests in isolation | `pytest tests/test_desk_coverage.py tests/test_desk_topup_compute.py tests/test_bar_index.py -q -o addopts=` | 40 passed in 3.28 s |
| Hermeticity | `stat` on `.data/{bar_index.db,bar_index.db-shm,bars,universe}` before/after | all four mtimes identical; `.data/bars` 128 files → 128 |
| J-01 still passing | `GET /research/desk/universe` over a copy of the real snapshot | 200, 1 snapshot, `latest` = `universe-2026-07-25-49b33fa31680`, 101 members, `integrity_errors: []`, shape `['integrity_errors','latest','snapshots']` unchanged |
| Coverage route, populated | `POST /research/desk/topup/compute` → poll → `GET /research/desk/coverage` | `done`, 12/12 pairs `fetched`; coverage 200 with 3/3 members × 4 timeframes `has_bars: true` |
| Coverage at real scale | 101-member snapshot, 1,212 indexed rows | **1.5 ms**, 34,264 B payload, zero `BarStore` calls |
| CLI warmer, real vendor | `python -m app.research.desk_topup_compute` ×4 | see T1 — exit 1 / exit 1 / exit 0 (4 fetched) / exit 0 (4 reused) |
| TC-13 capture | `diff kept-route-baseline-24.txt kept-route-after-24.txt` | identical; 24 rows; populated bodies |
| J-01 handler bytes | `git diff apps/backend/app/research/desk_routes.py` | zero `-`/`+` inside `fetch_universe`/`get_universe`; only docstring, imports, additions |
| Blueprint conformance | `runs/goal-session-desk/state/blueprint.md:94-95` | both Data-Contract rows present and matching the shipped payloads byte-for-byte; `assumptions.md` iter-2 entry present |
| Nav / UI | `app.meta.UI_ROUTES` | 2 rows: `['/', '/structure']` |

The dev handoff's claims were checked, not trusted; only the two count statements in T6 were
inaccurate, and no claim I checked was false. No handoff claim needed correcting as a result of this
audit (no fix invalidated one).

---

## 5. Recommended Next Step

**Proceed to J-03 (screen compute + append-only ledger).** J-02's DoD is met on independently
re-executed evidence — coverage truth-table incl. honest-empty, store-first proven against both
`FakeAdapter` *and* the real vendor, single-flight, cancel, resumability, `GET`-never-computes,
index-read latency measured at real scale, honest per-pair failure with the run continuing, suite
1240/8 over the 1210/8 floor, pin unchanged, J-01 unperturbed, 24/24 kept routes byte-identical. The
compute-manager pattern J-03 must copy is now proven in a second place, and coverage gives J-03 the
per-member × per-timeframe input it needs.

Carry these into the J-03 / J-04 specs (do not silently inherit them):

1. **Decide the "nothing new to record" outcome (B1)** before `/desk` renders top-up progress.
   Either add a fourth vocabulary value (e.g. `"unchanged"`, a blueprint Data-Contract edit) or
   have the desk layer classify HTTP 409 separately from real failures — but keep `"reused"`
   meaning *zero vendor calls*, since the store-first proof rests on it. Also decide whether the
   CLI should exit 1 for a run whose only "failures" are duplicates.
2. **Label freshness truthfully on `/desk` (B2).** `latest_window_end_utc` is "window last
   requested", not "last bar" — real `1w` data lags it by up to a week, and a delisted symbol
   reads as today-fresh forever. If a real staleness badge is wanted, source `covered_end_utc`
   from `BarStore.get` for the rendered rows (a display-layer read), not from `bar_index`.
3. **Add the three cheap `main()` tests (T1)** and one populated route-level coverage assertion
   (T2) when a nearby file is next touched — my manual runs are evidence for *this* iteration,
   not a regression net for the next one.
4. **Still outstanding from iter-1, unchanged:** the `edge_report_cache._config_content_hash`
   cold-cache latency (accepted, latency-only) must be warmed before J-04's browser pass, and
   `journey-scripts/J-07.json` step 8's async-text assertion still needs re-pointing at a
   statically-SSR'd string — both become live the moment `Frontend Present: yes` returns.
5. **No anti-goal violation was introduced.** No execution path, no new statistic/gate/strategy, no
   scheduler (every run is an explicit POST/CLI act), membership used only to select what to fetch,
   recordings append-only and immutable (the 409 that motivates B1 is that immutability working),
   suite keyless and hermetic, pin unmoved, `UI_ROUTES` still 2, MCP untouched at 15 tools.
