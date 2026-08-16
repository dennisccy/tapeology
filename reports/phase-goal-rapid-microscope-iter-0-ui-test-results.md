# Goal Iteration 0 (rapid-microscope) — UI Test Results

**Phase:** goal-rapid-microscope-iter-0
**Date:** 2026-08-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- This is the EXPECTED, BY-DESIGN result for this iteration. Iteration 0 of session
     `rapid-microscope` is an explicit verify-only baseline (Mode: baseline, zero source
     edits) opened immediately after Era 6 "The Referee" reached GOAL_ACHIEVED. Per the
     iteration spec's own BACKGROUND section: "J-01's readiness endpoint/UI sub-checks and
     all of J-02 through J-09 are expected to register FAILING at this snapshot... J-10's
     overall verdict is expected to land PARTIAL at best." None of this era's core deliverable
     modules exist anywhere under apps/backend/app/ yet — that is the correct, honest state of
     a freshly opened era before any of its ten journeys have been built. FAIL here records
     truthful baseline state, not a regression or a bug. -->

**Overall:** 0/10 journeys pass full Acceptance (0 skipped) — matches the iteration's own
predicted baseline exactly. All ten journeys were exercised; every sub-check that COULD
pass (transition artifacts, fingerprint pin, kept-surface rendering, backend suite health)
DID pass — only the not-yet-built Rapid-Microscope deliverables are absent, as designed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | smoke | P1 | Transition artifacts present + baseline metrics recorded + `GET /research/desk/micro/readiness` serves corpus data + `/desk` Microscope Readiness section renders it | Transition artifacts ALL present (verified); baseline metrics recorded (see "Reference data" section below for suite/fingerprint/SHA-256); readiness endpoint 404s (module not built); `/desk` has no Microscope Readiness section (confirmed absent via full-page text extract) | FAIL | `reports/qa/goal-rapid-microscope-iter-0-evidence/J-01-desk-readiness-absent.png` |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | happy-path | P1 | `observer=` kwarg on `DatasetStore.replay`; `micro_observer.py`/`micro_snapshots.py`/`micro_features.py` exist; snapshots endpoint lists 18/18 legacy snapshots | `DatasetStore.replay` signature is `(self, dataset_id: str, config: Config)` — no `observer=` kwarg; none of the three modules exist under `apps/backend/app/`; `GET /research/desk/micro/snapshots` → 404 | FAIL | none — no UI surface exists yet; verified via source inspection (`datasets.py:376`) + `find` + `curl` (see Actual) |
| UT-J-03 | Structure × flow — the join that never looks ahead | happy-path | P1 | `micro_join.py` exists; joinable-corpus count served on readiness endpoint | `micro_join.py` not found anywhere under `apps/backend/app/`; readiness endpoint itself 404s so no count is served | FAIL | none — no UI surface exists yet; verified via `find` + dependency on J-01's 404 |
| UT-J-04 | The Scout and the ledger — every trial on the record | happy-path | P1 | `scout_ledger.py`/`scout.py` exist; `GET /research/desk/micro/scout` serves a fixture-grid ledger | Neither file found under `apps/backend/app/`; `GET /research/desk/micro/scout` → 404 | FAIL | none — no UI surface exists yet; verified via `find` + `curl` |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | happy-path | P1 | `micro_accessor.py`/`walkforward.py` exist; `GET /research/desk/micro/walkforward` serves fold/sequence data | Neither file found under `apps/backend/app/`; `GET /research/desk/micro/walkforward` → 404 | FAIL | none — no UI surface exists yet; verified via `find` + `curl` |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | happy-path | P1 | Card-5.1 preservation fields (`conditions`/`exchange`) on `RawTrade`/`RawQuote`/`TradeEvent`/`QuoteEvent`; `tick_recorder.py`/`vault.py` exist; `GET /research/desk/micro/vault` serves shard/exposure state | `RawTrade` = `{epoch, price, size}` only; `RawQuote` = `{epoch, bid, ask, bid_size, ask_size}` only — no preservation fields; neither `tick_recorder.py` nor `vault.py` found; `GET /research/desk/micro/vault` → 404 | FAIL | none — no UI surface exists yet; verified via source inspection (`providers/adapters/base.py:64-82`) + `find` + `curl` |
| UT-J-07 | Graduation — provenance in, nothing laundered out | happy-path | P1 | `micro_graduation.py` exists implementing the 4-state graduation pipeline | Not found under `apps/backend/app/` | FAIL | none — no UI surface exists yet; verified via `find` |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | happy-path | P1 | `/desk` renders Scout Ledger, Walk-Forward, Validation Vault sections below Microscope Readiness; 4 new byte-identical MCP GET proxies; MCP contract bumped to v6 (26 tools) | None of the 3 new section headings found anywhere in `/desk`'s full-page text extract; `EXPECTED_TOOLS` in `test_mcp_server.py` lists exactly 22 tools (unchanged from Era 6), none of `desk_micro_readiness`/`desk_scout`/`desk_walkforward`/`desk_vault` present | FAIL | `reports/qa/goal-rapid-microscope-iter-0-evidence/J-08-desk-sections-absent.png` |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | happy-path | P1 | Three ledgered study specs (range-wall failed aggression; delta divergence at level tests; capitulation exhaustion) with registration timestamps preceding any outcome read | No scout ledger exists (depends on J-04, itself absent); no pilot-study spec files found anywhere under `apps/backend/app/` | FAIL | none — no UI surface exists yet; verified via `find` (no scout/pilot-study artifacts of any kind) |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | Full TR-1…TR-22 trap suite green; deterministic-rerun check byte-identical; full backend suite passes ≥ era-open baseline with 0 regressions; fingerprint prints `08e471b10130e1e2`; referee SHA-256 listing recorded; every kept surface (`/`, `/structure`, `/desk` shipped sections) browser-verified as shipped | TR-1…TR-22 suite and deterministic-rerun check do not exist yet (expected — J-10's remaining work). Everything else PASSED: backend suite 2,691 passed/8 skipped/0 failed (exact match to the documented era-open baseline), fingerprint = `08e471b10130e1e2` (matches pin exactly), referee SHA-256 listing recorded for all 6 `referee_*.py` files (this iteration's baseline for every later re-check), cockpit `/` loads with shipped Live/Historical/Simulated toggle + Watch input, `/structure` loads with Tradable Map/Case Studies/Edge Report/Fetch Bars/Registry/Comparison all rendering shipped copy, `/desk` loads with Screen/Playbook/Playbook Evidence/Referee Registry/Referee Adjudications/Referee Runs all present | FAIL | `reports/qa/goal-rapid-microscope-iter-0-evidence/J-10-cockpit.png`, `J-10-structure.png`, `J-10-desk.png` |

---

## Passed Tests

None — no journey's full Acceptance line was met at this snapshot (expected; see verdict
note above). Sub-checks that DID pass are itemized per-journey in Failed Tests below,
since the results table only carries one verdict per journey and partial credit is not
representable there.

---

## Failed Tests

### UT-J-01 — The era transition stands — the corpus truth on the record
**Verdict:** FAIL (expected/by-design — steps 3–4 are explicitly OUT OF SCOPE this iteration)
**Failure:** `GET /research/desk/micro/readiness` returns HTTP 404 (module `micro_readiness.py`
does not exist); the `/desk` page's full-page text extract contains no "Microscope Readiness"
heading or any readiness-shaped content.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-0-evidence/J-01-desk-readiness-absent.png`

**Steps taken:**
1. Verified transition artifacts on `main`/`goal/rapid-microscope`:
   - `docs/goal-archive/goal-2026-08-16.md` exists (75,422 bytes); its title line reads
     "Era 6: The Referee" — confirmed it IS the Referee constitution.
   - `docs/rapid-validation-spec.md` exists (45,411 bytes).
   - `docs/research-directions.md` carries the "RAPID-MICROSCOPE OPENING NOTE (2026-08-16,
     operator pivot...)" at line 1089, the Card-5.2/Era-15/units (T12) dated amendments at
     lines 166, 296-297, 328-330, 494, 1744-1745, and the appended era-6 status row at line
     2008 ("2026-08-16 | 6 (The Referee) | referee | done | ...").
   - `project-extensions/proposer-guidance.md` carries the "§5.3 amendments applied
     2026-08-16" note at line 6-7.
   All PRESENT — sub-check 1 fully satisfied.
2. Ran the full backend suite, fingerprint check, and referee SHA-256 listing (results
   recorded under UT-J-10 to avoid duplication — same commands serve both journeys).
3. Probed `GET /research/desk/micro/readiness` via curl against the store-scoped rig
   (`http://localhost:8301`) → HTTP 404. Confirms `micro_readiness.py` is not implemented.
4. Navigated to `http://localhost:3301/desk` with Chrome MCP, extracted full-page text.
   Content present: Desk Screen, Playbook (with signal families), Playbook Evidence
   (collapsed), Referee Registry (collapsed), Referee Adjudications (collapsed), Referee
   Runs (collapsed). No "Microscope Readiness" text anywhere on the page.

**Expected:** Readiness endpoint serves `distinct_symbol_days: 12`, `session_equivalents ≈
3.0`, per-shard `exploratory`/`hand_assigned` tags, and a floors table (every pilot study
`floor_unmet`); `/desk` renders a Microscope Readiness section with those same values.
**Actual:** Endpoint 404s; no such UI section exists. Transition-artifact sub-check (step 1)
and baseline-metric recording (step 2) both hold true; steps 3-4 are the not-yet-built
portion the iteration spec explicitly places out of scope.

---

### UT-J-02 — The micro observer — one pass, prefix-honest, benchmarked
**Verdict:** FAIL (expected/by-design — entirely OUT OF SCOPE this iteration)
**Failure:** No `observer=` kwarg on `DatasetStore.replay`; none of `micro_observer.py`,
`micro_snapshots.py`, `micro_features.py` exist; `GET /research/desk/micro/snapshots` → 404.
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. Read `apps/backend/app/research/datasets.py:376` — `def replay(self, dataset_id: str,
   config: Config) -> Iterator[EngineSnapshot]:` — two parameters only, no `observer=`.
2. `find apps/backend/app -iname "micro_observer.py" -o -iname "micro_snapshots.py" -o
   -iname "micro_features.py"` → no matches.
3. `curl http://localhost:8301/research/desk/micro/snapshots` → HTTP 404.

**Expected:** TR-1/TR-17/TR-18/TR-7 traps pass; 18/18 legacy snapshots exist; snapshots
endpoint lists them; engine equivalence and golden trace pass byte-unmodified.
**Actual:** None of the underlying code exists yet — the whole journey is future work,
exactly as this iteration's spec states.

---

### UT-J-03 — Structure × flow — the join that never looks ahead
**Verdict:** FAIL (expected/by-design)
**Failure:** `micro_join.py` does not exist; no joinable-corpus count is served anywhere
(depends on the readiness endpoint, itself absent).
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. `find apps/backend/app -iname "micro_join.py"` → no matches.
2. Confirmed (via J-01) that `GET /research/desk/micro/readiness` 404s, so no
   joinable-corpus count can be served on it.

**Expected:** A committed fixture join reproduces hand-computed feature-at-trigger values;
joinable-corpus count served on readiness with per-study breakdown; lookahead assertion and
detector/context-byte-freeze guards pass.
**Actual:** No implementation exists yet.

---

### UT-J-04 — The Scout and the ledger — every trial on the record
**Verdict:** FAIL (expected/by-design)
**Failure:** Neither `scout_ledger.py` nor `scout.py` exists; `GET
/research/desk/micro/scout` → 404.
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. `find apps/backend/app -iname "scout.py" -o -iname "scout_ledger.py"` → no matches.
2. `curl http://localhost:8301/research/desk/micro/scout` → HTTP 404.
3. Confirmed no stray ledger or pilot-study files exist anywhere under `apps/backend/app`
   via a broader `find` (also serves J-09).

**Expected:** TR-8/9/10/11 pass; fixture family ledger shows every variant with decision and
reason; served screen carries `evidence_class`, best-of-N line, economic column.
**Actual:** No implementation exists yet.

---

### UT-J-05 — The walk-forward engine — chronology, fences, and the diagnostic run
**Verdict:** FAIL (expected/by-design)
**Failure:** Neither `micro_accessor.py` nor `walkforward.py` exists; `GET
/research/desk/micro/walkforward` → 404.
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. `find apps/backend/app -iname "micro_accessor.py" -o -iname "walkforward.py"` → no
   matches.
2. `curl http://localhost:8301/research/desk/micro/walkforward` → HTTP 404.

**Expected:** TR-3/5/6/13/14/15/16/21/22 pass; 155-session diagnostic run completes with 5
folds / 100 validation sessions, every fold/sequence labeled
`historical_exposed_diagnostic`; tick-family fold request returns typed floor-refusal
naming `11 < 105`.
**Actual:** No implementation exists yet.

---

### UT-J-06 — The recorder and the Vault — new tape, sealed at birth
**Verdict:** FAIL (expected/by-design)
**Failure:** Card-5.1 preservation fields absent from the raw event dataclasses; neither
`tick_recorder.py` nor `vault.py` exists; `GET /research/desk/micro/vault` → 404.
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. Read `apps/backend/app/providers/adapters/base.py:64-82` — `RawTrade` = `{epoch, price,
   size}`; `RawQuote` = `{epoch, bid, ask, bid_size, ask_size}`. No `conditions`/`exchange`
   fields on either dataclass, confirming the Card-5.1 preservation prerequisite (J-06 step
   1) has not landed.
2. `find apps/backend/app -iname "tick_recorder.py" -o -iname "vault.py"` → no matches.
3. `curl http://localhost:8301/research/desk/micro/vault` → HTTP 404.

**Expected:** TR-2/4/12/19/20 pass; legacy datasets/fixtures load byte-identically; tranche
exists on disk meeting every §7.6 minimum; sealed subset exists with zero pre-exposure
reads; 12 legacy symbol-days remain `exploratory`.
**Actual:** No implementation exists yet — this journey's step 4 is also explicitly an
operator-gated act reserved for a later iteration, never this one.

---

### UT-J-07 — Graduation — provenance in, nothing laundered out
**Verdict:** FAIL (expected/by-design)
**Failure:** `micro_graduation.py` does not exist.
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. `find apps/backend/app -iname "micro_graduation.py"` → no matches.

**Expected:** Fixture walk produces a validating `referee_handoff_ready` bundle whose
provenance lists every trial/fold/shard including failures; diagnostic-only and
failed-sealed refusals counter-tested.
**Actual:** No implementation exists yet.

---

### UT-J-08 — The surface and MCP v6 — the funnel is visible
**Verdict:** FAIL (expected/by-design)
**Failure:** `/desk` has no Scout Ledger, Walk-Forward, or Validation Vault sections; MCP
tool count is 22 (unchanged), not the target 26; none of `desk_micro_readiness`,
`desk_scout`, `desk_walkforward`, `desk_vault` exist as tool names.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-0-evidence/J-08-desk-sections-absent.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`, extracted full-page text (same navigation
   serves J-01). Text contains only shipped sections (Screen, Playbook, Playbook Evidence,
   Referee Registry, Referee Adjudications, Referee Runs) — no "Scout Ledger", "Walk-Forward",
   or "Validation Vault" heading anywhere.
2. Read `apps/backend/tests/test_mcp_server.py:60` — `EXPECTED_TOOLS` is a 22-tuple:
   `tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups,
   backtests, strategies, edge_report, desk_universe, desk_screen, desk_forward,
   desk_playbook, desk_playbook_evidence, desk_referee, desk_referee_registry, pnl_ledger,
   taxonomy, ui_route_map, get_endpoint`. No `desk_micro_*` names present.

**Expected:** All four new sections render served values verbatim (element-captured
screenshots); the four new tools return byte-identical bodies to their GET routes; 26-tool
contract test and replay-script static sweep pass.
**Actual:** None of the four sections or tools exist yet; MCP surface unchanged at 22 tools
(v5), matching the Era-6 close state exactly.

---

### UT-J-09 — The pilot studies — three predeclared questions, honest answers
**Verdict:** FAIL (expected/by-design)
**Failure:** No ledgered pilot-study specs of any kind exist (the Scout ledger itself is
absent).
**Evidence:** none (no UI surface exists for this journey at this snapshot)

**Steps taken:**
1. `find apps/backend/app -iname "*scout*ledger*" -o -iname "*pilot*stud*"` → no matches.
2. Cross-referenced J-04's confirmed absence of `scout_ledger.py`/`scout.py` — since the
   ledger module itself doesn't exist, no study (range-wall failed aggression / delta
   divergence at level tests / capitulation exhaustion) can be registered in it.

**Expected:** Three ledgered study families exist with predeclared specs whose registration
timestamps precede their first outcome read; each serves evidence class, denominators,
disclosures, economic column; each carries a decision in the closed vocabulary.
**Actual:** No implementation exists yet — this is J-04/J-05's downstream work.

---

### UT-J-10 — The kept product stands — traps armed, sentinel green
**Verdict:** FAIL (partial — the browser-testable sentinel PASSED in full; only the
not-yet-built TR-1…TR-22 trap suite and deterministic-rerun check are missing, and those are
explicitly this journey's remaining future work per the iteration spec)
**Failure:** The TR-1…TR-22 leakage-trap suite and the deterministic-rerun check do not
exist yet, so J-10's full Acceptance line is not met. Every OTHER component of the
Acceptance line — full backend suite, fingerprint, referee SHA-256 listing, and every kept
UI surface — was independently verified and PASSED.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-0-evidence/J-10-cockpit.png`,
`reports/qa/goal-rapid-microscope-iter-0-evidence/J-10-structure.png`,
`reports/qa/goal-rapid-microscope-iter-0-evidence/J-10-desk.png`

**Steps taken:**
1. Ran `cd apps/backend && .venv/bin/python -m pytest -q` to completion. (First attempt with
   the bare `.venv/bin/pytest -q` entry point failed at collection with `ModuleNotFoundError:
   No module named 'app'` — a `sys.path` artifact of invoking the console-script directly
   rather than via `python -m`, not a code defect; the `python -m pytest` re-run collected
   and ran normally with zero import errors.) See the exact final tally in the paragraph
   below this list.
2. Checked `Config().config_fingerprint()` → `08e471b10130e1e2` — matches the pinned value
   exactly.
3. Computed SHA-256 of every `apps/backend/app/research/referee_*.py` file (6 files:
   `referee_adjudicate.py`, `referee_evidence.py`, `referee_null.py`, `referee_registry.py`,
   `referee_routes.py`, `referee_stats.py`) — recorded below as the iteration-0 reference
   listing for every later re-check.
4. Navigated to `http://localhost:3301/` (cockpit) — loads correctly: Live/Historical/
   Simulated toggle, ticker Watch input, idle default state ("No ticker watched", "Try:
   SIM-BUYER"). Screenshot taken.
5. Navigated to `http://localhost:3301/structure` — loads correctly: Tradable Map, Case
   Studies, Edge Report, Fetch Bars, Registry (champion = v1/default, all three strategies
   v1/structure_tape/structure_tape_map with their full parameter tables), Comparison — all
   rendering their correct shipped empty-state copy. Screenshot taken (full page).
6. Navigated to `http://localhost:3301/desk` — loads correctly: Screen, Playbook (with the
   full 8-family signal list: ORB/JBE/DBI/cup-and-handle/capitulation/range-trade/
   double-top/double-bottom), Playbook Evidence, Referee Registry, Referee Adjudications,
   Referee Runs (the latter four rendered collapsed with their ▸ disclosure triangles —
   header text confirmed present in the full-page extract; not expanded this pass under the
   iteration's lean-mode budget). Screenshot taken (full page).
7. Searched for the TR-1…TR-22 trap suite and any deterministic-rerun check script/test —
   none exist (consistent with J-02 through J-09's absence — the traps ship alongside the
   modules they guard).

**Backend suite result:** **2,691 passed / 8 skipped / 0 failed / 0 errors** (2,699 collected
total), exit code 0. This is an EXACT match to the "2,691 pass / 8 skip at authoring" figure
already recorded in `docs/goal.md` §Success Criteria #1 for this era's opening — confirming
zero regressions against the documented era-open baseline.

*Methodology note:* `.venv/bin/python -m pytest -q` produced its dot-grid progress output
but its final one-line summary (the usual "`N passed, M skipped in Ts`") did not appear in
the captured log — reproduced even under `--collect-only -q`, so it is an environment/plugin
quirk of this pytest install, not a redirection artifact (disk space was not the cause: 172G
free). No `conftest.py` under `apps/backend/` overrides `pytest_terminal_summary`. Because
the summary line was unavailable, the pass/skip/fail count above was independently
reconstructed by tallying every per-test status character (`.`/`s`/`F`/`E`/`x`/`X`) directly
from the captured dot-grid — 2,691 `.`, 8 `s`, zero of any failure/error character. (First
invocation attempt, the bare `.venv/bin/pytest -q` console-script, failed at collection with
`ModuleNotFoundError: No module named 'app'` — a `sys.path` artifact of the console-script
entry point, not a code defect; re-running via `python -m pytest` collected and ran
normally.)
**Expected:** Full suite passes at count ≥ era-open baseline (2,691 pass / 8 skip) with 0
regressions; fingerprint `08e471b10130e1e2`; referee SHA-256 listing recorded; TR-1…TR-22
green; deterministic rerun byte-identical; every kept surface screenshot-verified.
**Actual:** Suite green with 0 failures, exactly at the documented baseline (2,691/8);
fingerprint matches exactly; referee listing recorded (6/6 files, hashes above); every kept
UI surface loads and renders its shipped content correctly. TR suite and rerun check are the
only missing piece, and they are explicitly out of scope for this baseline iteration (they
ship alongside J-02 through J-07's modules in later iterations).

---

## Skipped Tests

None. Frontend was running (HTTP 200 at `http://localhost:3301`) and Chrome MCP was
available throughout; every journey was exercised to a determinate PASS/FAIL sub-check
result.

---

## Reference data recorded this iteration (era-open baseline)

- **Backend suite:** **2,691 passed / 8 skipped / 0 failed** (exit code 0) — see UT-J-10
  above for the methodology note on how this was tallied. Exact match to the
  `docs/goal.md`-documented era-open figure.
- **`Config().config_fingerprint()`:** `08e471b10130e1e2` (matches the pin stated in
  `docs/goal.md` §Foundation invariants #1 and the iter spec's expected value).
- **Referee module SHA-256 listing** (iteration-0 reference for every later re-check; all
  six are standard 64-hex-character digests):
  - `referee_adjudicate.py` — `6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c`
  - `referee_evidence.py` — `482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5`
  - `referee_null.py` — `34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603`
  - `referee_registry.py` — `03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99`
  - `referee_routes.py` — `0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140`
  - `referee_stats.py` — `fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c`
- **MCP tool count:** 22 (unchanged from Era 6 close; target 26 per J-08).
- **Git branch:** `goal/rapid-microscope`, HEAD `bbfcfd0` ("docs(goal): pre-implementation
  consistency correction (rapid-microscope preflight)").

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL (store-scoped rig):** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`),
  headless, pinned profile/CDP port — no profile or headed-mode overrides used.
- **Test Date:** 2026-08-17
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-0-evidence/`
- **Golden replay scripts:** none written this iteration — every journey's full Acceptance
  currently reads FAIL (expected, by design), and the golden-script protocol only applies to
  journeys verified PASS. `runs/goal-session-rapid-microscope/journey-scripts/` remains
  empty; a future iteration will populate it once J-01/J-08/J-10 (the browser-testable
  journeys) actually pass.
