# goal-observation-contract-iter-6 Audit Report

**Date:** 2026-09-05
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-06's guard suite is real, non-vacuous work and J-04's long-open browser-evidence gap is genuinely
closed this round — I re-read the two paused-reload screenshots myself and they show an identical
`observation_hash` with differing `generated_at_utc` / `artifact_hash`, on the served JSON, not a
404 page. One of the five guard mechanisms, however, shipped weaker than every document that
specifies it (`docs/goal.md` J-06 step 3 and Trap Coverage item 44, the phase spec's mechanism 5 /
TC-9, and the plan): it checked call-site *location* instead of *re-settling*, and one live call
site (`WatchManager.stop`) sits inside the allowed location while never re-settling. I fixed that
in the iteration's own test module and re-verified (guard module 23/23, full suite 4067 passed / 8
skipped / 0 failed, exit 0). The remaining gaps are evidence-bookkeeping, not product defects:
J-05's own journey row was shed for budget (though every J-05 acceptance clause was independently
exercised this round under other test ids, which I verified), and two QA/replay rows carry
mis-paired or structurally vacuous evidence.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the mutator-call-site guard checked call-site location, not re-settling —
and a live call site escapes the invariant it is supposed to protect**

Pre-fix `_is_allowed_mutator_call_site` (`apps/backend/tests/test_tape_observation_guards.py:583`,
original numbering) returned `True` for *any* method of `WatchManager`:

```python
if path_name == "watch_manager.py" and class_name == "WatchManager":
    return True
```

Every document that specifies this mechanism asks for more than location:

- `docs/goal.md:705` (J-06 step 3): "the mutator-call-site guard (every `TapeEngine` mutator call
  under `app/` lives in `watch_manager.py` methods **that re-settle**, or in `DatasetStore.replay`)";
- `docs/goal.md:913` (Required Trap Coverage item 44): "Every engine-mutator call site under `app/`
  **re-settles through the manager** or is the unserved dataset replay";
- phase spec IN SCOPE mechanism 5 and TC-9 (`docs/phases/goal-observation-contract-iter-6.md`);
- `runs/goal-observation-contract-iter-6/plan.md:33-34` and `:136-137`.

The gap is not theoretical. `WatchManager.stop` mutates the engine at
`apps/backend/app/watch_manager.py:477` (`engine.set_stream_status("closed",
end_reason="watch_stopped")`) and is the **one** mutator-calling method in that file whose body
never calls `self._settle(...)` — I enumerated all 28 call sites and their enclosing methods with
the module's own AST helpers (`_mutator_call_sites`); only `stop` lacks a settle. The shipped guard
reported zero violations. I also confirmed the escape hatch by splicing a new `WatchManager` method
that mutates and never settles into a copy of the real `watch_manager.py`: pre-fix the guard
returned **no violation**.

`stop` itself is not a product bug: it deletes the engine from `self._engines` in the same method,
and `get_observation_source` (`apps/backend/app/watch_manager.py:415`) looks the engine up first and
returns `None`, so the route 404s and no stale settled pair is reachable. The defect is that the
guard could not tell that legitimate case from an illegitimate one — it never asked the question.

**Fix applied** (test-only, inside this iteration's own new module; no frozen or protected file
touched): `_settling_method_names()` (`:621`) derives the allowed methods from the scanned file's
own AST (`self._settle(...)` call sites); `_is_allowed_mutator_call_site` (`:641`) now admits a
`WatchManager` method only if it re-settles or is in `_NON_SETTLING_CARVE_OUTS` (`:608`) — a single
documented `("watch_manager.py", "WatchManager", "stop")` triple with the deletion/404 reasoning
written next to it. Two tests added: `test_settling_method_detection_is_not_vacuous_and_names_one_
documented_carve_out` (`:695`) pins both the detected settling set and the exact carve-out set, so
a future widening of either is a visible, deliberate act; and
`test_counterexample_mutator_call_site_guard_detects_a_non_settling_watch_manager_method` (`:713`)
perturbs the REAL `watch_manager.py` (splice inside the real class body) and asserts the guard now
names the offending method.

**Verification (post-fix):**
`cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q` →
23 progress dots, 0 F/E, exit 0 (21 before the fix — I ran the pre-fix baseline first).
Full suite `pytest tests/ -q` → **4067 passed, 8 skipped, 0 failed, 0 errors, exit 0** (iter-5
baseline 4044 + this module's 23 tests; tallied from the `-q` progress characters, the iter-0
lesson's method). `cd apps/frontend && npx tsc --noEmit` → 0 errors, exit 0 (my own run).

**B2 — GAP (observation): the mutator scan only sees a receiver literally named `engine`**

`_MutatorCallVisitor.visit_Call` matches `Name(id="engine")` receivers only
(`apps/backend/tests/test_tape_observation_guards.py:580-591`). I confirmed the hole empirically —
the same `process_event` call written as `tape_engine.process_event(event)` in a copy of `main.py`
returns **no violation** — and confirmed it is not live: a grep of *every* call to the six mutator
names anywhere under `apps/backend/app/` returns 32 sites, all accounted for (28 `engine.*` in
`watch_manager.py`, 1 in `research/datasets.py:491`, plus `manager.pause`/`manager.resume` in
`main.py:526,539` which are `WatchManager` methods and `self._history.set_epoch_anchor` in
`engine/tape_engine.py:251` which is `HistoryBuffer`). The reviewer filed the same point as a NOTE.
Not fixed: broadening the receiver match would need an allowlist for those three legitimate
same-name collisions, and inventing that policy is beyond this iteration's scope.

**B3 — GAP: the external-system reference guard is narrower than "under `apps/`"**

`_apps_source_files` (`:353`) scans only `.py/.ts/.tsx/.js` and skips `fixtures` and `.data`
directories, while the spec (and `docs/goal.md`) say "under `apps/`" without a file-type limit — a
`workstation`/`trendora`/`tensteps` reference in, say, a JSON, `.env`, `.md` or fixture file under
`apps/` would not be seen. Verified nothing is hidden today: a case-insensitive grep for all three
tokens across **every** file type under `apps/` (minus `.venv`/`node_modules`/`.next`/`__pycache__`)
matches exactly one file — the guard module itself, which is `SELF`-excluded by design.

**B4 — GAP: mechanism 1 blanks every `test_counterexample_*` body in the scanned modules**

`_stripped_python_source` (`:192`) removes comments, all docstrings **and** every
`test_counterexample_*` function body before scanning (`_counterexample_function_nodes`, `:171`).
The rationale is sound (those bodies deliberately seed the very violations the lint hunts), and I
measured the blast radius: 0.0% of `observation_contract.py` (it has no counterexample functions —
the production contract module is scanned in full), 5.8%–17.5% of each of the five test modules, and
the live-served-artifact leg is not stripped at all. The narrower `_KNOWN_PATTERN_LIST_EXCEPTIONS`
(`:144`) is load-bearing and correctly scoped: without it the scan reports exactly
`['trade_allowed', 'READY', 'NO_TRADE', 'NO_VERDICT', 'PENDING_CONDITION']` against
`test_tape_observation_lifecycle_feed.py:47`'s module-scope `ACTIONABILITY_TOKENS` constant; with it,
zero — and the exemption is keyed per file and per token, so the same tokens elsewhere still trip.
Residual: within that one file the five tokens are exempt everywhere, not only on line 47.

**B5 — GAP: the real-provider isolation guard is a per-module AST scan, not an import/call graph**

`_alpaca_references` (`:485`) inspects `Name` / `Attribute` / `ImportFrom` nodes of each
`test_tape_observation_*` module; TC-7 says "scans their import/call graph". A module that reached
`AlpacaAdapter` transitively (through a helper module) would not be flagged. Also, the gated-smoke
carve-out (`_is_gated_smoke_module`, `:497`, which correctly requires **both** the env-var name and
a `skipif`) is exercised only by a synthetic fixture, because no `TAPEOLOGY_REAL_PROVIDER_SMOKE`
module exists this era — the dev handoff discloses this honestly. Sim-only operation is separately
protected by the era's other guards, so I am not raising this above GAP.

### Frontend Findings

**F1 — OBSERVATION: nothing changed, and that is verified, not asserted.** `git status --porcelain`
over `apps/frontend` is empty; `tsc --noEmit` is clean on my own run; the browser rows show `/`,
`/structure` and `/desk` rendering with an unchanged 3-link nav (UT-02/UT-03/UT-10), and UT-11
records that the only "observation" string anywhere in the rendered HTML is pre-existing Cockpit
empty-state copy. No new panel, link or control.

### Test / Evidence Findings

**T1 — GAP: the English-only counter-test is the weakest of the five.**
`test_counterexample_english_only_guard_detects_a_non_ascii_value` (`:470`) adds a hand-written
`"bid–absorption"` to a *copy of the real enum-value set* rather than perturbing a real source file
or the fetched artifact the way the other four counter-tests do. It still drives the real scan
function over a real-derived container, so it is not tautological — but it is the one place the
iter-3/iter-4 "perturb the REAL thing" lesson is honoured in spirit more than in letter. (The scan
targets themselves are strong: `field_partition_map()` yields 45 paths / 51 key segments including
nested ones, and the enum leg reads `CONFIG` / `data_feed_for_scenario` rather than literals.)

**T2 — GAP: QA's J-04 numbers do not match QA's own J-04 screenshots.**
`reports/qa/goal-observation-contract-iter-6-qa.md` §6 quotes `generated_at_utc`
`02:53:22.689303Z` / `artifact_hash 785e9caf…` and `02:53:27.278785Z` / `84692a00…`, then cites
`TC-04-observation-reload-1.png` / `-2.png` as the evidence. Those images actually show
`02:53:30.472082Z` / `0edc238d…` and `02:53:35.681001Z` / `34f6f62f…`. Both pairs carry the same
`observation_hash` (`f524002d5b1a22015e8a68b07694dd6248779320a27ee5c94f450c7ee3bcc938`) and both
satisfy the acceptance clause, so the conclusion is sound — the report simply pairs curl-read
numbers with screenshots from two later reloads. The DoD clause itself is met: I read both PNGs and
each shows the paused served JSON (`"stream_status":"paused","paused":true`), identical
`observation_hash`, differing `generated_at_utc` and `artifact_hash`, with
`"config_fingerprint":"08e471b10130e1e2"` legible in-frame.

**T3 — GAP: J-05's own journey row was shed for budget, and the QA report does not say so.**
`reports/phase-goal-observation-contract-iter-6-ui-test-results.md` ends with
`UT-J-05 … DEFERRED-BUDGET` ("not run this iteration"), and the ux-regression reviewer was likewise
shed (`…-ux-regression.md`: UX-REGRESSION-SKIPPED, budget). The QA report nonetheless reports
"Total Checks Passed: 10/10 … Blockers: NONE" without mentioning either. The DoD asks that J-05
"remain green — verified via the LLM browser-qa lane". Mitigation, verified by me rather than
assumed: every J-05 acceptance clause *was* exercised this round under other ids — UT-04 (served
JSON with `"schema_version":"tape-observation-v1"`; I read the screenshot), UT-07 (404 body
`{"detail":"Ticker 'ZZZZ' is not being watched"}`; I read the screenshot), and
`tests/test_tape_observation_route.py` inside the green full suite. So J-05's substance is covered;
its journey-row bookkeeping is not.

**T4 — GAP: one deterministic-replay row is a vacuous PASS.**
The replay lane reported `UT-J-02 … journey replayed end-to-end; all expects held → PASS`. Its
golden script `runs/goal-session-observation-contract/journey-scripts/J-02.json` contains seven
steps that never leave the Cockpit (`goto /`, Simulated, fill ticker, Watch, Pause, Resume, Stop) —
it never opens `/tape/SIM-BIDABS/observation`, so it cannot observe a single thing J-02 asserts, and
its evidence file `J-02-verify.png` shows the post-Stop "No ticker watched" cockpit. The spec
anticipated the lane's false-FAILs (J-01/J-03: `J-01-verify.png` and `J-03-verify.png` are one
byte-identical Next.js 404 page, md5 `cdcf05e2…` — I opened it); this is the mirror-image risk, a
false-PASS, and is worth recording before the golden scripts are ever regenerated. J-02's real
verification this round is the LLM lane's own UT-06 row, whose screenshot I read and which matches
its recorded values exactly.

**T5 — OBSERVATION: J-02's "own steps" screenshot is byte-identical to UT-04/UT-09/UT-J-01's.**
`UT-06-result.png`, `UT-04-result.png`, `UT-09-result.png` and `UT-J-01-result.png` share md5
`9730432a…`, and the UT-06 row simultaneously says "same GET as UT-04" and "not borrowed from
UT-04/UT-09". The substance the DoD asked for is present — UT-06 is J-02's own row with its own
independently recorded five fields, and I confirmed all five are legible in that image
(`observed_at_utc "2024-01-02T14:30:58.000000Z"`, `available_at_utc null`, `availability_basis
"simulated_not_applicable"`, `timing.settled_at_utc "2026-09-05T03:11:37.544829Z"`,
`generated_at_utc "2026-09-05T03:11:37.549943Z"`) — so this is a wording inconsistency, not borrowed
evidence in the iteration-5 sense.

---

## 3. Domain Assessment

The era's core discipline — an artifact that *projects* engine state rather than recomputing it, and
a manager that settles snapshot-and-time as one atomic pair — holds up under reading, and this
iteration's guards mostly protect it honestly.

The strongest parts of the delivered module are the ones that touch reality: mechanism 1's third leg
fetches a live artifact from a **real uvicorn subprocess** (watch → settle → pause → GET, asserting
HTTP 200) rather than a `TestClient`, so the copy-discipline and compound-identifier scans run
against bytes a consumer would actually receive; and four of the five counter-tests perturb real
source, a real fetched artifact or the real `app/` tree. The non-vacuity tests are real too (the
five-module glob is pinned by name and proven to exclude SELF; the `apps/` file list must exceed 100
files and contain `main.py`; the mutator scan must find >10 `WatchManager` sites and a
`DatasetStore.replay` site) — this is the class of check that would have caught a path bug silently
scanning nothing.

The weak spot was mechanism 5, and it is instructive: the module, the handoff and the test name all
described what was built ("lives inside a `WatchManager` method") accurately, so nobody misreported
anything — the drift was between an honestly-described weaker check and a specification that asked
for a stronger one, in the exact place the era's Constitution §2 invariant lives. A location-only
guard would have stayed green through precisely the regression the guard exists to catch (a new
manager method that mutates the engine and forgets to re-settle, leaving `get_observation_source`
handing out a snapshot that no longer matches the engine). That is now closed, with the one
legitimate exception (`stop`) named and justified in code rather than silently absorbed.

Production code was untouched this iteration and I verified that independently rather than trusting
the handoff: `git status --porcelain` is empty for `apps/backend/app`, `apps/frontend` and all nine
protected guard test files; `apps/backend/app/config.py` is unmodified (no new `Config` field); the
served `config_fingerprint` reads `08e471b10130e1e2` in three separate browser screenshots; the
anti-goal ledger in `state/journey-history.json` is `"anti_goal_violations": []`; and the
store-scope guard reports the operator's real `.data` store byte-identical before and after the run.
The one logged decomposer assumption (no second recompute guard in this module) checks out — the
recompute guard and its two counter-tests are where the assumption says they are,
`test_tape_observation_projection.py:160-173`.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_tape_observation_guards.py` | Mutator-call-site guard now enforces the specified predicate: `_settling_method_names()` derives re-settling methods from real `self._settle(...)` AST call sites; `_is_allowed_mutator_call_site` admits a `WatchManager` method only if it re-settles or is the single documented `_NON_SETTLING_CARVE_OUTS` entry (`WatchManager.stop`, which deletes the engine in the same method); module docstring corrected to describe the stronger check |
| 2 | Important | `apps/backend/tests/test_tape_observation_guards.py` | Added `test_settling_method_detection_is_not_vacuous_and_names_one_documented_carve_out` (pins both the detected settling set and the exact carve-out set) and `test_counterexample_mutator_call_site_guard_detects_a_non_settling_watch_manager_method` (perturbs the real `watch_manager.py` by splicing a non-settling mutator method into the real class body) |
| 3 | — | `docs/handoffs/goal-observation-contract-iter-6-dev.md` | Amendment note: the handoff's "21 tests / 4065 passed" counts are superseded by 23 tests / 4067 passed after fixes 1-2; all other handoff claims re-verified and left standing |

**Post-fix verification evidence:**
- `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q` → 23
  progress dots, no `F`/`E`, exit 0 (pre-fix baseline run by me first: 21 dots, exit 0).
- `cd apps/backend && .venv/bin/python -m pytest tests/ -q` → **passed=4067 skipped=8 failed=0
  errors=0**, exit 0 (progress-character tally; total collected 4075 = 4067 + 8).
- `cd apps/frontend && npx tsc --noEmit` → 0 errors, exit 0.
- Diff re-read: the change is confined to mechanism 5's predicate, its two new tests and the
  matching docstring line; no production file, no protected guard file, no frontend file, nothing
  outside this iteration's own new module.

---

## 5. Recommended Next Step

Proceed. J-06 and J-04 are met on evidence I re-derived myself, and the four required-still-passing
journeys are covered (J-05 through UT-04/UT-07 plus the route suite rather than its own journey row
— see T3, which the evaluator should record as an evidence-bookkeeping gap, not a regression).

Before the era is declared complete, three cheap items are worth queuing rather than doing now:
(1) run J-05's own numbered steps once so its journey row carries this iteration's evidence;
(2) when the replay harness's `normalize_url` backend-origin limitation is finally fixed, regenerate
`J-02.json` — today it passes without ever reaching the artifact (T4), which is the more dangerous
half of that harness bug; (3) fold B2's receiver-name assumption into the guard (an explicit
three-entry allowlist for the known non-`TapeEngine` collisions) so the mutator scan can prove it
sees *every* call site rather than every call site that happens to be named `engine`.
