# goal-desk-iter-14 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-10's product capability is genuinely built and genuinely proven: the drift classifier is pure
composition over `BarStore`/`BarIndex`'s existing public reads, `BarIndex.reindex()` is the only
repair path in the tree outside its own test, the run ledger is append-only/checksummed with one
writer, the compute manager is single-flight/pollable/cancellable, and the `/desk` section + trigger
render and work — verified by opening the code, the run records on disk, and the screenshots, not by
trusting a handoff. Every sentinel I re-ran myself holds (full suite exit 0, fingerprint
`08e471b10130e1e2`, MCP `EXPECTED_TOOLS` = 17, `git diff --stat` empty on all ten named files).
Two IMPORTANT problems sit in the EVIDENCE trail rather than the product: the QA lane ran the real
ambient-store reconciliation plus a new ambient screen compute — both explicitly out of scope for
this iteration's gates — and its TC-17/TC-18 screenshots do not show the states it certified. Both
are now corrected in the record; the acceptance itself is met by the later browser-QA lane's own
same-rig artifacts, which I opened and confirmed.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (disclosed, not reversible): the QA lane ran the real ambient-store reconciliation
and a new ambient screen compute, which this spec put OUT OF SCOPE.**
`docs/phases/goal-desk-iter-14.md:225-227` excludes "Running the real ~88-pair AMBIENT-store
reconciliation as part of this iteration's automated gates"; NOTES:349-351 makes the evidence
protocol binding ("On ONE fresh scoped copy of `.data/` — never the ambient store"); the same file's
BACKGROUND:104-106 carries iter-10's lesson ("Any screen computed for this iteration's evidence must
run on a FRESH scoped copy of `.data/`, never the target the J-01–J-09 goldens replay against").
It happened anyway, and the artifacts are on disk:
- `apps/backend/.data/index_reconcile_runs/reconcile-2026-07-28-43857811211f.json` — `started_utc`
  `2026-07-28T21:26:52Z`, `series_on_disk: 369`, `rows_indexed 281 → 369`, `drift_before` 88
  unindexed → `drift_after` 0. Those are goal.md's own ambient numbers, not the fixture rig's.
- `apps/backend/.data/screen/screen-2026-07-27-3ad3c57aa6ba.json` — created `2026-07-28T21:30:16Z`,
  new `bar_store_signature` `350c85d18b1ff234`, now the ambient `latest`.
Timestamps line up exactly with the QA lane's own two screenshots (`TC-17…png` 21:26Z,
`TC-18…png` 21:30Z) and with its TC-12 row naming `screen-2026-07-27-3ad3c57aa6ba`.

*Impact, measured rather than assumed:* bounded, and nothing is corrupted or lost.
`find apps/backend/.data/bars -name '*.json' -newermt 2026-07-27 | wc -l` → `0` of 369 files: the
repair was index-only exactly as designed. The ambient index went 281 → 369 rows (verified by direct
`sqlite3` count) — i.e. it was REPAIRED, which is the feature working. The new screen carries
identical `63` rows / `38` skipped and the same first row (BRK-B) as its predecessor
`936543601e75`; only the coverage badges and the signature differ. I checked every golden's
assertions against that (`runs/goal-session-desk/journey-scripts/*.json`): they assert structural or
dated strings only ("Desk", "coverage", "tick evidence", "Class A", "Config fingerprint",
"Universe snapshot", "basis", "d before as-of", the 2026-06-22/2026-07-25 history banners,
"No top-up runs recorded yet." — and no ambient `topup_runs` directory exists, so that one still
holds). No golden assertion is at risk from the ambient change.

*Not reverted, deliberately.* Deleting the ambient run record or the new screen snapshot would
itself breach the critical anti-goal "Snapshots are append-only and pinned … nothing is silently
refetched, backfilled, recomputed in place, or rewritten" (`docs/phases/goal-desk-iter-14.md:24-27`).
goal.md's own J-10 rationale says the ambient reconciliation is "an operator-run act, reported
honestly as run-or-not-run" — so the correct remedy is disclosure, which is applied here and appended
to the QA report. I was unsure between IMPORTANT and GAP and took the higher level: an explicit
out-of-scope rail was crossed and the effect on a shared, immutable-by-policy store is permanent.

**B2 — GAP: a `failed` reconciliation run is durably recorded with zeros and no reason.**
`apps/backend/app/research/desk_index_reconcile.py:474-487` — on the `except` path `_record_run` is
called with `result=None`, writing `series_on_disk: 0`, `rows_indexed_before/after: 0` and empty
drift for a store that may hold 369 series. The failure text lives only on the process-scoped
snapshot (`:496`), so after a restart the ledger row reads like a measurement of zero rather than
"unknown". Covered by its own test (`test_an_unexpected_crash_resolves_state_failed_and_records_a
_zeroed_run`), so it is intended, and `state: "failed"` is rendered beside the zeros in the UI table.
Not fixed: the registered Data Contract row (`runs/goal-session-desk/state/blueprint.md:142`) fixes
the record's field set, and adding an `error` field would break this iteration's own DoD requirement
that the served shape match it byte-for-byte. Worth a contract amendment in a later iteration.

**B3 — GAP: cancellation has exactly one observation point.**
`desk_index_reconcile.py:175-184` checks `should_abort()` only between classify and reindex. A cancel
arriving during `reindex()` or the verify pass is silently ineffective: the repair completes and the
run resolves `"done"` (`:499`). On the scoped rig the whole walk took 5.5 s (21:58:35.35 →
21:58:40.88), so the miss window is most of the run. Honest in the ledger (the record says what
actually happened) but the operator gets no signal that their cancel arrived too late. The
Top-up precedent checks per pair, so this control is materially coarser than the one it mirrors.

**B4 — GAP: the terminal snapshot is published before the durable record is written.**
`desk_index_reconcile.py:500-501` resolves the snapshot, then writes the record. The page polls every
700 ms and refetches the runs list the moment it sees a terminal state
(`apps/frontend/app/desk/page.tsx:1444-1456`), so a refetch that wins the race renders
"No reconciliation run recorded yet." for a run that just succeeded, until the next page load. The
window is one small file write, and this mirrors `desk_topup_compute.py:327-329` exactly, so it is a
precedent-consistent limitation rather than a new defect.

**B5 — OBSERVATION: `stale_checksum_rows` never compares checksums.**
`desk_index_reconcile.py:138-140` populates that bucket purely from corrupt-file stems
(`:124`); `BarIndexHit.checksum` is never compared against the healthy record's `checksum`. An index
row whose stored checksum disagreed with a HEALTHY file would therefore be reported as "no drift"
even though `reindex()` would rewrite it — the ledger would under-report what it repaired. The case
is remote (series ids are `uuid.uuid4().hex`, `bars.py:639`, and files are immutable) and the spec's
own TC-3 defines the bucket exactly as implemented, so this is a naming/coverage note, not a defect.

**B6 — OBSERVATION: three full store walks per run.** `classify_drift` calls
`store.list(include_bars=False)` (`:120`), `run_reconcile` calls it a second time only to count
`series_on_disk` (`:172-173`), and `BarIndex.reindex` calls `store.list()` a third time *with*
candles. The stat-keyed cache absorbs most of it (5.5 s over 369 series), but a `healthy` return from
`classify_drift` would remove one walk with zero contract change.

### Frontend Findings

**F1 — GAP: no feedback when a cancel misses its window.**
`apps/frontend/app/desk/page.tsx:1075-1147` — clicking Cancel sets `reconcileCancelRequested` and
shows "Cancelling…" (`:1138`); if the run then resolves `"done"` (B3), `isRunning` flips false, the
whole running block unmounts, and the operator sees a completed run with no note that the cancel had
no effect. Nothing false is displayed — the run genuinely did complete — but the requested action
silently disappears. Sibling controls avoid this by cancelling between units of work.

**F2 — OBSERVATION: the reconciliation section renders every drift entry, unbounded.**
`page.tsx` `DriftList` renders one `<li>` per entry with no cap; the scoped rig's first run produced
95 rows and the ambient store would produce 88. Legible today (verified in
`UT-07-UT-08-lit-badge-and-reconciliation.png`) and honest by design — noted only because `/desk` now
carries three stacked history panels, which the ux-regression review also flagged as a watch item.

### Test Findings

**T1 — IMPORTANT (fixed by correction, not by deletion): the QA report's TC-17/TC-18 rows certify
states its cited screenshots do not show.**
I opened both files. `reports/qa/goal-desk-iter-14-evidence/TC-17-empty-reconciliation.png` and
`TC-18-populated-reconciliation.png` show a scrolled BRIEFING table of the 101-member AMBIENT
universe (BRK-B/DHR/HD/IBM/NFLX/…) — the "Index Reconciliation" section is not in either frame at
all, so neither the empty-state text (TC-17's pass criterion) nor the drift counts (TC-18's) are
visible. The `drift_before=88, drift_after=0` figure quoted in the QA table is the ambient run's
number (B1); the fixture-scoped rig's own first run is `95 → 0`
(`…/desk-iter14-scoped-qa/.data/index_reconcile_runs/reconcile-2026-07-28-cfddc344cfe2.json`). Per
`.claude/judgment-rubrics.md` §6, the screenshot wins over the claim.
*The acceptance itself is still met*, by the later browser-QA lane's own artifacts on the scoped rig,
in the required one-way-door order — both of which I opened and confirmed:
- `UT-02-before-empty-and-dark-badge.png` — AAPL row with `1d` dark beside `1h`/`4h`/`1w` lit AND
  "INDEX RECONCILIATION → No reconciliation run recorded yet." in one full-page frame, captured
  ~21:57Z with `GET …/reconcile/runs` verified `latest: null`, one minute before the first scoped run
  at 21:58:35Z.
- `UT-07-UT-08-lit-badge-and-reconciliation.png` — the same AAPL row with all four badges lit AND the
  populated panel (`reconcile-2026-07-28-cfddc344cfe2`, `done`, `369 series on disk`, `274 → 369`,
  "Drift before (95)" naming `AAPL 1d …`, "Drift after (0) · no drift") in one frame.
That lane flagged the discrepancy itself (`…-ui-test-results.md`, UT-08's Actual column). Fixed by
appending a labelled auditor correction to `reports/qa/goal-desk-iter-14-qa.md` (verdict line
untouched, no evidence file deleted or renamed).

**T2 — IMPORTANT (fixed): the `[NEW]`-flagged demo walkthrough's step-02 frame contradicted its own
narration (TC-19).**
`reports/demo/goal-desk-iter-14/step-02.png` was byte-identical to `step-01.png` and `step-06.png`
(md5 `d64f057c…`) — a post-repair frame showing lit badges and no reconciliation panel — while step
02 narrates "the page says so plainly … one price badge sits dark". Root cause is the one-way door:
browser QA had already recorded the first real reconciliation on that rig hours earlier, so no live
recording of that step can ever reproduce the empty state there. `demo.json`'s own step-02 `capture`
block anticipated exactly this and named the remedy (splice the same-rig pre-run capture), citing
iteration 13's precedent where the auditor performed it; `demo-results.md` carried the automatic soft
note but the splice had not been done. Fixed — see §4. After the splice the walkthrough reads
02 (empty, spliced genuine pre-run frame) → 03 (trigger) → 04 (populated detail:
`state: done`, three runs, drift lists) → 05 (fresh screen) → 06 (badge lit), each frame matching its
narration, in order, all from the same scoped rig. I opened step-04 and step-06 to confirm.

**T3 — GAP: two replay artifacts for the same lane disagree, and the failing one is a false
negative.** `reports/phase-goal-desk-iter-14-regression-replay-results.md` reports **FAIL, 0/8**,
while the merged `…-ui-test-results.md` reports **PASS, 21/21**. Opening the cited evidence settles
it: `reports/qa/goal-desk-iter-14-evidence/J-01-verify.png` shows the page rendering
"Backend unreachable — is the API running? / Nothing cached and nothing fabricated is shown in its
place." — the replay ran against a stopped backend, so all eight failed at step 01/02. Genuine
green replays on a live rig exist and are cited:
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.154299/golden-reverify-results.md` (8/8 PASS,
23:14) and `…/j10-golden-results.md` (J-10 1/1 PASS, 23:16), plus the dev lane's
`reports/phase-goal-desk-iter-14-smoke-replay-results.md` (8/8). Left in place — the failing artifact
is honest about what it observed; it just needs this context so no reader scores it as a regression.
(Silver lining: that same screenshot is a clean proof that the new section degrades honestly when the
backend is down.)

**T4 — OBSERVATION: the dev handoff's test count is wrong.** It claims 44 tests in
`test_desk_index_reconcile.py` (`docs/handoffs/goal-desk-iter-14-dev.md:70`); collection reports
`tests/test_desk_index_reconcile.py: 42`. The reviewer already noted this; no functional impact.

**T5 — OBSERVATION: TC-20's endpoint-level clause is met at the store layer only.**
The spec's TC-20 says the corrupted file's failure is "surfaced as an explicit, named error" when the
runs endpoint is called; `desk_routes.py:505` discards `ReconcileRunStore.list()`'s `errors` channel
(`records, _errors = store.list()`), exactly as `get_topup_runs` does. This is the correct build:
the registered Data Contract fixes the response to `{"runs", "latest"}`, adding a third key would
break the byte-for-byte DoD item, and the spec's own OUT OF SCOPE list defers the sibling
"top-up-runs `integrity_errors` disclosure". Consequence to record: a corrupted reconcile run-record
file is invisible to the operator in the UI — it is dropped from `runs`/`latest` and named only in
the store's return value, which nothing consumes. Tested both ways
(`test_tc20_corrupted_run_record_file_surfaces_explicitly…` at the store,
`test_tc20_get_reconcile_runs_survives_a_corrupted_run_record_file…` at the route).

---

## 3. Domain Assessment

The core logic is correct and, unusually, achieves its "zero new accessor" constraint honestly. The
filename-stem insight (`{Path(e["file"]).stem for e in errors}`, `desk_index_reconcile.py:124`) is
load-bearing and I verified it holds: `BarStore._path` is `root/f"{id}.json"` (`bars.py:273-274`) and
`BarStore.list` reports errors as `{"file": path.name, …}` (`bars.py:389`), so the stem genuinely is
the `series_id`. Because `list()` puts each file in `healthy` XOR `errors`, the three buckets are
mutually exclusive by construction rather than by tie-breaking — the test at
`test_desk_index_reconcile.py:174-201` asserts exactly that, including the no-id-in-two-buckets
property.

The SSOT claim survives inspection. `git diff --stat` is empty on `bar_index.py`, `bars.py`,
`tradability.py`, `levels.py`, `desk_coverage.py`, `StructureChart.tsx`, `PriceChart.tsx`,
`config.py`, `meta.py`, `app/mcp/__init__.py` (my own run, not the handoff's). `grep -rn "\.reindex("`
over `app/`, `scripts/`, `tests/` finds exactly one production call site — `desk_index_reconcile.py:188`
— plus `test_bar_index.py`'s own five: there is no second index-building path. Coverage still flows
solely from `desk_coverage` over `bar_index`, which is why the repair shows up in the badges with
zero UI code change, and why the post-repair screen naturally lands under a new `bar_store_signature`
(proved in the unit test at `:295-320` and again live: `460ccfc8aed5f2db` → `643a581230fc110a` across
UT-02 and UT-08).

Test quality is high and the assertions are tight — exact dict equality on all three buckets, exact
`store_errors == expected_errors` byte-comparison against `BarStore.list()`'s own errors,
`public_methods == {"root", "list", "record"}` as a structural proof that no update/delete exists,
byte-identity of the first run's file across a second run, and a real threading handshake (not
sleeps) for the single-flight/cancel paths. The manager tests monkeypatch the module-level
`classify_drift` name to create a deterministic slow path, which is the same seam
`test_desk_topup_compute.py` uses. Two soft spots: the cancel test only exercises the abort point
that exists (B3's coarseness is untested because it is unspecified), and TC-4's coverage flip is
asserted through `get_desk_coverage(...)` directly rather than through `GET /research/desk/coverage`
— defensible, since that function is the endpoint's sole owner, and the live UT-02→UT-08 pair proves
the HTTP path anyway.

Copy discipline holds: I re-ran `test_copy_discipline.py` (unmodified) together with the new file —
72 tests, exit 0. The new section's strings are counts, labels and bucket descriptions
("series on disk, no index row"), with no advice, imperative or prediction language.

Sentinels re-verified independently by me, not read from a handoff: full backend suite `exit=0`;
`Config().config_fingerprint()` → `08e471b10130e1e2`; `EXPECTED_TOOLS` parsed to exactly 17 names
with no reconcile tool; the two blueprint Data-Contract rows
(`runs/goal-session-desk/state/blueprint.md:142-143`) match the shipped shapes field-for-field,
including the meta-only projection (`desk_routes.py:485-492`) and `latest` carrying
`drift_before`/`drift_after`/`store_errors`.

DEFINITION OF DONE, item by item: TC-17/TC-18 — **met**, by `UT-02…png` and `UT-07-UT-08…png`, not by
the files named `TC-17/TC-18` (T1). J-01–J-09 still green — **met**, by the 8/8 golden re-verify on a
live rig plus the LLM lane, with T3's false-negative artifact explained. No anti-goal violation —
**met** in the code (zero diff, append-only, no scheduler, no MCP tool, lint green); B1 is a breach of
an out-of-scope rail, not of an anti-goal. TC-1–TC-16/TC-20 + suite green — **met**. Fingerprint and
17 tools — **met**. Data-Contract rows matched byte-for-byte — **met**. TC-19 — **met after this
audit's fix** (T2). Dev handoff naming the scoped rig — **met**.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/demo/goal-desk-iter-14/step-02.png` | Spliced the genuine same-rig pre-run capture (`reports/qa/goal-desk-iter-14-evidence/UT-02-before-empty-and-dark-badge.png`) over the live-recorded frame, so the `[NEW]`-flagged J-10 walkthrough's empty-state step shows the state it narrates (TC-19). The remedy the demo script's own `capture` block specifies, and iteration 13's precedent |
| 2 | Important | `reports/phase-goal-desk-iter-14-demo-results.md` | Added two soft notes: the splice's provenance (source file, md5, capture time, scoped root, one-way-door reason) and the fact that steps 01/06 share one frame and why both narrations are true of it |
| 3 | Important | `reports/qa/goal-desk-iter-14-qa.md` | Appended a labelled "Auditor correction" section: the TC-17/TC-18 screenshots do not show the certified states, which artifacts actually satisfy those criteria, and that the run behind them executed against the ambient store (T1, B1). Verdict line and original text untouched |

**Verification of my own fixes.**
1. `md5sum` after the splice: `step-02.png` = `f15f778e824656f8fda644b07dec794b` = the named source
   file, and every other frame's md5 is unchanged (`step-01` `d64f057c…`, `03` `d377cb2a…`,
   `04` `2b86c8c4…`, `05` `e5f94286…`, `06` `d64f057c…`, `09` `e833fac2…`, `13` `835dacef…`).
2. Downstream parser re-run:
   `render_iteration_summary._parse_demo_results(demo-results.md)` → `("RECORDED_WITH_NOTES", [8 steps
   parsed, step 02 → step-02.png, `is_new: true`])` — my edit did not break the HTML renderer's input.
3. `grep -n "Verdict" reports/qa/goal-desk-iter-14-qa.md` → line 8 `**Verdict:** PASS` still the first
   and only machine-parsed verdict line; `artifact_schemas.py:141`'s regex is unaffected by the
   appended prose.
4. Scope check on my own diff: three artifact files, zero source files, zero test files. No product
   code was touched by this audit, and nothing was deleted or renamed.
5. No handoff claim was invalidated by these fixes; the dev handoff's own "one-way door" reasoning is
   what fix 1 completes.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator with J-10 scored `passing`, reading TC-17/TC-18 against
`UT-02-before-empty-and-dark-badge.png` and `UT-07-UT-08-lit-badge-and-reconciliation.png` (per T1),
and treating `…-regression-replay-results.md`'s 0/8 as the dead-backend false negative it is
(per T3, with the 8/8 live re-verify cited).

Two items to carry forward, neither blocking this iteration:

1. **Disclose the ambient reconciliation as the operator act it now is.** goal.md's J-10 rationale
   asks for exactly this reporting. The ambient `bar_index.db` is now repaired (281 → 369 rows) and
   `apps/backend/.data/screen/screen-2026-07-27-3ad3c57aa6ba.json` is the new ambient `latest`; the
   88 pairs goal.md cites — NFLX `1h`/`1d`, META `1h`/`1d`, NVDA `1h`/`1d`, MSFT `4h` — now read
   correctly there. Do not delete either record (append-only). A future iteration that replays the
   goldens against the ambient store should expect the repaired badges, and its lanes should be told,
   in the dispatch text, which rig to touch — B1 happened because one lane was not.
2. **Backlog the ledger honesty gaps** for a contract-amending iteration: a failure reason on a
   `failed` run record (B2), cancel observation points inside the repair walk (B3), and an
   `integrity_errors` channel on the runs endpoint (T5) — which is the same disclosure the proposer
   already has backlogged for the top-up ledger, so the two should land together rather than
   piecemeal.
