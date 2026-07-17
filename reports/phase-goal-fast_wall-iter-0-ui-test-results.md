# Goal Iteration goal-fast_wall-iter-0 — UI Test Results

**Phase:** goal-fast_wall-iter-0
**Date:** 2026-07-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- This is a BASELINE assessment iteration (Mode: baseline, iter-0 of session `fast_wall`).
     Per docs/phases/goal-fast_wall-iter-0.md, J-01 through J-06 are EXPECTED to FAIL (none of
     the interlude's capabilities have been built yet — zero code changes this iteration) and
     J-07 (the foundation regression sentinel) is EXPECTED to PASS. The verdict above tracks
     J-07 — the one journey that gates "does the existing, already-shipped product still work" —
     which passed with strong evidence. J-01-J-06 FAILing is the correct, desired baseline
     recording, not a QA or pipeline malfunction; see the Baseline Context section below. -->

**Overall:** 1/7 journeys PASS (J-07), 6/7 journeys FAIL as expected for a pre-build baseline (J-01–J-06), 0 SKIPPED at the journey level (one specific live-page-load sub-check was withheld for a documented operational-safety reason — see below — but every journey still received a fully evidenced PASS/FAIL verdict, none left indeterminate).

---

## ⚠️ Safety-driven scope note: `/structure` was NOT live-loaded this iteration

Before testing, I checked whether it was safe to navigate the browser to `/structure` (needed for
J-01's and J-04's live render checks, J-06's page-ready timing check, and part of J-07's spot-check
list). It is **not**, against the currently running backend, and I deliberately did not do it. Evidence:

- The backend on port 8301 has **no dataset-dir override env var** (checked
  `/proc/<pid>/environ`) — it serves the **real corpus**: `apps/backend/.data/datasets` = 882MB,
  **18 registered datasets** (confirmed via `GET /research/datasets`), integrity clean.
- `apps/frontend/app/structure/page.tsx:1228-1255` fires `fetchEdgeReport()` **unconditionally**
  inside the page's mount-time `useEffect`, alongside `fetchDatasets()`/`fetchSetups()` — so
  merely navigating to `/structure` triggers `GET /research/edge-report` with no user action
  required.
- `apps/backend/app/research/routes.py:2110-2115` (`get_edge_report`) calls
  `run_strategy_comparison_report(...)` unconditionally on that GET, and
  `edge_report_cache.py` currently exposes only `get_or_compute` (no `lookup`) — so a cache miss
  computes **synchronously inside the request**.
- `.data/edge_report_cache.db` is 12KB and unmodified since before this backend started — i.e.
  cold for the real registry (the real compute "has never finished," per `docs/goal.md`).
- `docs/goal.md`'s own Vision section documents the measured consequence of triggering this on
  the real corpus: **"the backend worker pinned at 98% CPU for hours after a single page visit,
  degrading every other endpoint through the GIL."** Because uvicorn here runs a single process
  with no `--workers` flag, a synchronous CPU-bound compute inside an `async def` route blocks
  the entire event loop — freezing every other request (including health checks) for the
  duration. There is no cancel capability yet (that is literally what J-04 would add).
- `ps aux` at the start of this run showed **three other active `claude` processes** on this
  shared machine, plus this goal-mode pipeline itself depending on the same backend for
  subsequent iterations. Pinning it for "hours" (documented, not speculative) would actively
  break this and other concurrent work.

Given `docs/phases/goal-fast_wall-iter-0.md`'s own verification-action text explicitly allows
this exact substitution — *"a compute-spy is not required at baseline; an observed hang/timeout
**or a direct code citation** ... is sufficient evidence"* — and explicitly marks *"performing
any mutating recompute against the real 882MB corpus"* as **out of scope**, I used the source
citations above (independently re-verified by me via `grep`/`Read`, not merely copied from the
decomposer's notes) in place of a live trigger. This is a considered operational-safety decision,
not a tooling failure — flagging it here because it is new information relevant to how future
iterations should probe `/structure` (e.g. a scoped/keyless dataset dir for browser-QA use would
avoid the hazard entirely).

All other pages (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) do **not** touch
the edge-report path and were live-verified normally below.

---

## Baseline Context

This is iteration 0 (`Mode: baseline`) of the brand-new `fast_wall` goal-mode session — a
verify-only iteration with **zero source changes** (`git diff --stat apps/` confirmed empty
throughout this QA pass). Its purpose is to record which of J-01–J-07 already pass/fail against
the current (post-`tradable_wall`, pre-interlude) codebase. Per the iteration spec: *"J-01 through
J-06 are expected to fail at baseline... J-07 (foundation regression sentinel) is expected to
pass."* All 7 results below match that prediction exactly.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Stop the bleeding — `GET /research/edge-report` never computes | baseline-probe | P2 | Cold-cache GET returns instant not-computed payload; zero sweep invocations | Route unconditionally calls `run_strategy_comparison_report`; cache class has no `lookup`/`compute_and_publish`; frontend has no not-computed panel. Feature absent. | FAIL (expected) | code citations below; no screenshot (live trigger withheld — see safety note) |
| UT-J-02 | Stores stop re-reading — verified-content caches + durable dataset index | baseline-probe | P2 | `GET /research/datasets` serves from a stat-keyed cache in <1s warm | No stat-keyed cache in `bars.py`/`datasets.py`; no `dataset_index.py`. Live-measured `GET /research/datasets`: **30.13s / 8,588 bytes / 18 datasets**, matching `docs/goal.md`'s documented 31.4s almost exactly. | FAIL (expected) | `reports/qa/goal-fast_wall-iter-0-evidence/J-02-datasets-latency.txt` |
| UT-J-03 | The arm memo — per-tick levels recompute becomes ~100 memo hits/session | baseline-probe | P2 | `structure_tape`/`structure_tape_map` arming uses `_StructureArmMemo` | No `level_change_points`, `basis_day_key`, or `_StructureArmMemo` anywhere in `levels.py`/`tradability.py`/`backtests.py`. Feature absent. | FAIL (expected) | code citation below; no browser surface exists for this journey |
| UT-J-04 | The operator-run compute — button, background job, CLI warmer | baseline-probe | P2 | `/structure` shows a "Compute edge report" button; POST/GET/cancel routes exist | No `edge_report_compute.py`; no `/research/edge-report/compute` route; no "Compute edge report" text anywhere in `structure/page.tsx`. Feature absent. | FAIL (expected) | code citations below; no screenshot (live trigger withheld — see safety note) |
| UT-J-05 | The sweep becomes resumable and parallel | baseline-probe | P2 | `EdgeReportBacktestCache` + `run_pair` provider seam exist | No `EdgeReportBacktestCache`, no `run_pair` in `edge_report.py`. Feature absent. | FAIL (expected) | code citation below; no browser surface exists for this journey |
| UT-J-06 | Restarts stop hurting — durable setups scan cache | baseline-probe | P2 | Restart-surviving scan cache; `/structure` fully ready within 10s | No `setups_scan_cache.py`; `setups.py`'s only cache is still the fragile in-process `_SCAN_CACHE` keyed by `id(config)` (era 5B, wiped every restart). Live-measured `GET /research/setups`: **268.95s (4m29s)** cold, ruling out sub-10s ready today. | FAIL (expected) | `reports/qa/goal-fast_wall-iter-0-evidence/J-06-setups-latency.txt` |
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression | P1 | Full suite green; fingerprint pinned; era-1–5B surfaces behave as shipped | Suite: **1392 passed, 7 skipped, 0 failed** (exit 0). `config_fingerprint` = `4d665603569b9dbf` (confirmed via direct call AND on-page). Cockpit: SIM-BUYER→Buyer Control, SIM-SELLER→Seller Control, both with correct event-log text. `/journal`, `/journal/[id]`, `/studies`, `/performance` all render correctly with frozen register text intact. `/structure` not live-checked this iteration (safety note above). | PASS | `reports/qa/goal-fast_wall-iter-0-evidence/J-07-*.png` (5 screenshots) |

---

## Passed Tests

### UT-J-07 — The foundation is unchanged (regression sentinel)
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-fast_wall-iter-0-evidence/J-07-cockpit-sim-buyer.png`
- `reports/qa/goal-fast_wall-iter-0-evidence/J-07-cockpit-sim-seller.png`
- `reports/qa/goal-fast_wall-iter-0-evidence/J-07-journal-detail.png`
- `reports/qa/goal-fast_wall-iter-0-evidence/J-07-studies.png`
- `reports/qa/goal-fast_wall-iter-0-evidence/J-07-performance.png`

**Step 1 — full backend suite + engine equivalence.** Ran `apps/backend/.venv/bin/python -m
pytest tests/` twice (once for a clean run, once to capture the authoritative summary line):
**"1392 passed, 7 skipped, 0 failed"** (second run: `433.05s`, exit code 0 both times). No test
deleted or weakened (this is a verify-only iteration; `git diff --stat apps/` empty throughout).

**Step 2 — `config_fingerprint`.** Confirmed `4d665603569b9dbf` two independent ways: (a) direct
Python call `Config().config_fingerprint()`, and (b) live on the `/journal/[id]` detail page,
which prints "Config fingerprint: 4d665603569b9dbf" verbatim in the UI. Matches the frozen value
exactly.

**Step 3 — sim cockpit (`SIM-BUYER` → `buyer_control`, `SIM-SELLER` → `seller_control`).**
Navigated to `/`, typed `SIM-BUYER`, clicked Watch: Tape State panel read **"Buyer Control"**
(confidence 0.932), the `scenario: buyer_control` badge was present, and the event log read
"Tape state changed to buyer_control" — settlement confirmed. Stopped, switched to `SIM-SELLER`,
clicked Watch: Tape State panel read **"Seller Control"** (confidence 0.934), `scenario:
seller_control` badge present, event log read "Tape state changed to seller_control" — settlement
confirmed. Both match the acceptance text verbatim.

**Step 4 — `/journal` + `/journal/[id]`.** `/journal` lists persisted theses (SIM-SELLER,
SIM-BUYER, both dated 07-07-2026, restart-proof per the page's own copy). Clicked into the
SIM-BUYER entry: `/journal/e35c467375c14858b76a1e65f0c67e5a` renders the full "Review" panel —
thesis setup ("Trend continuation", LONG), invalidation price, declared timestamp, bound source
(`buyer_control`), feed (`SIM`), and the config fingerprint, plus a "What you expected... MET"
section.

**Step 5 — `/studies`.** Loads with heading "Replay studies" and the documented register copy
("journaled MEASUREMENTS of a replay... never a profitability claim... never pooled across
[feed/fingerprint]"); the reference-window/seeded-sim/symbol-window source options are present
and unchanged.

**Step 6 — `/performance`.** Loads with the PnL ledger; the frozen register banner **"simulated —
assumed fees/slippage — not indicative of live results"** renders verbatim, and the
"founding-baseline-strategy-v1-default" row is present with its net R / net $ / n columns.

**Step 7 — `/structure` era-5/5B behaviors.** NOT executed live this iteration — see the safety
note at the top of this report. No regression is claimed or implied for `/structure`; this is an
honest gap in this iteration's live coverage, not a passing or failing observation.

Golden replay script written: `runs/goal-session-fast_wall/journey-scripts/J-07.json` (covers
steps 3–6 above; linted clean via `demo_runner.py --mode lint`). `/structure` is intentionally
excluded from the script since it was not actually exercised this run.

---

## Failed Tests

<!-- All six of these are the EXPECTED, CORRECT baseline result for a pre-build iteration — see
     "Baseline Context" above. Each entry cites the exact code evidence gathered THIS session
     (independently grep/Read-verified by browser-qa-agent, not merely copied from the
     decomposer's notes) proving the described capability does not yet exist. -->

### UT-J-01 — Stop the bleeding — `GET /research/edge-report` never computes
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** The route computes inline on a cold cache; no honest
not-computed payload exists yet.

**Evidence:**
- `apps/backend/app/research/routes.py:2110-2115` — `get_edge_report` calls
  `run_strategy_comparison_report(registry.store, dataset_store, bar_store, registry.config,
  cache=cache)` unconditionally, `except EdgeReportError` only.
- `apps/backend/app/research/edge_report_cache.py` — only `get_or_compute` exists (grep for
  `def lookup`, `def compute_and_publish` → no matches).
- `apps/backend/app/research/edge_report.py` — no `peek_strategy_comparison_report` (grep → no
  matches).
- `apps/frontend/app/structure/page.tsx` — no `not_computed` / "Compute edge report" text
  anywhere (grep → no matches in source, only unrelated `.next` build-cache directory names).

**Expected:** Cold-cache GET returns an honest `status: "not_computed"` payload within an
interactive budget, with zero backtest invocations, and `/structure` renders a distinct
"Edge report not computed yet." panel.
**Actual:** Feature does not exist; the route is byte-identical to its pre-interlude (era-5B)
shape. Live browser confirmation of the resulting hang was deliberately not attempted — see the
safety note. Static code evidence alone is conclusive and sufficient per the iteration spec's own
allowance.

---

### UT-J-02 — Stores stop re-reading — verified-content caches + durable dataset index
**Verdict:** FAIL (expected at baseline)

**Evidence:**
- `grep -n "st_mtime_ns\|st_size" apps/backend/app/research/bars.py
  apps/backend/app/research/datasets.py` → no matches (no stat-keyed cache).
- `find . -name dataset_index.py` → no matches.
- **Live-measured** `GET http://localhost:8301/research/datasets`: `HTTP 200`, **30.13s**,
  8,588 bytes, 18 datasets, 0 integrity errors — reproducing `docs/goal.md`'s documented "31.4s
  to return 8.6KB" figure to within half a second, freshly measured this session (not merely
  cited from prior notes). Saved to
  `reports/qa/goal-fast_wall-iter-0-evidence/J-02-datasets-latency.txt`.

**Expected:** A second `list()`/`GET /research/datasets` call performs zero file re-reads and
answers sub-second warm.
**Actual:** No caching layer exists; every call re-reads/re-hashes the full 882MB corpus, exactly
as documented. Not a browser-interactive journey (goal.md tags J-02 "Keyless; automated" — no UI
surface renders this directly); verified via API probe + source inspection instead of a page
interaction.

---

### UT-J-03 — The arm memo
**Verdict:** FAIL (expected at baseline)

**Evidence:** `grep -rn "level_change_points\|basis_day_key\|_StructureArmMemo"
apps/backend/app/research/levels.py apps/backend/app/research/tradability.py
apps/backend/app/research/backtests.py` → no matches.

**Expected:** `structure_tape`/`structure_tape_map` arming checks are served from a per-run memo
keyed by change-point interval / UTC day.
**Actual:** Feature does not exist. Not a browser-interactive journey (goal.md tags J-03
"Keyless; automated" — pure backend memoization, no UI surface).

---

### UT-J-04 — The operator-run compute — button, background job, CLI warmer
**Verdict:** FAIL (expected at baseline)

**Evidence:**
- `find . -name edge_report_compute.py` → no matches.
- `grep -n "edge-report/compute" apps/backend/app/research/routes.py` → no matches (no
  POST/GET/cancel routes).
- `grep -n "Compute edge report" apps/frontend/app/structure/page.tsx` → no matches.

**Expected:** `/structure`'s not-computed panel shows a "Compute edge report" button that POSTs
the trigger and polls progress.
**Actual:** Feature does not exist at any layer (manager, routes, CLI, or button). Live DOM
confirmation of the button's absence was not attempted (loading `/structure` would fire the
dangerous `GET /research/edge-report` regardless of what I intended to check — see safety note);
the source-level absence is unambiguous and was independently re-verified via grep this session.

---

### UT-J-05 — The sweep becomes resumable and parallel
**Verdict:** FAIL (expected at baseline)

**Evidence:** `grep -rn "EdgeReportBacktestCache\|run_pair"
apps/backend/app/research/edge_report.py` → no matches.

**Expected:** A durable per-(dataset×strategy) cache and a `run_pair` provider seam exist,
enabling resume + a parallel CLI provider.
**Actual:** Feature does not exist. Not a browser-interactive journey (goal.md tags J-05 "Keyless
on fixtures; automated" — no UI surface).

---

### UT-J-06 — Restarts stop hurting — the durable setups scan cache
**Verdict:** FAIL (expected at baseline)

**Evidence:**
- `find . -name setups_scan_cache.py` → no matches.
- `apps/backend/app/research/setups.py:403` — the cache key is still `key = (id(config),
  _store_signature(store))`, the fragile identity-based key era 5B shipped; `_SCAN_CACHE` is the
  sole (in-process, restart-wiped) cache.

**Expected:** A durable sibling SQLite scan cache survives a simulated restart with zero
rescans, and `/structure` reaches ready state within 10s of navigation on the real corpus.
**Actual:** Feature does not exist; only the existing restart-wiped in-process cache is present.
**Live-measured** `GET http://localhost:8301/research/setups`: `HTTP 200`, **268.95s (4m29s)**,
4,497,772 bytes on the real corpus (18 datasets) — a bounded but slow cold scan, consistent with
"minutes when cold" in `docs/goal.md` and with no durable cache existing to shortcut it. The live
"`/structure` page ready within 10s" timing check was not measured this iteration — it requires
loading `/structure`, which is withheld for the documented safety reason (loading it fires the
same-page-mount `GET /research/edge-report` that would pin the backend for hours regardless of
which specific sub-check I was trying to observe) — but the measured 4m29s cold-scan latency
alone already rules out a sub-10s ready state today, independent of that specific page-load risk.

---

## Skipped Tests

None at the journey level — every one of J-01–J-07 received a fully evidenced verdict. (The
narrower `/structure` live-page-load sub-checks inside J-01/J-04/J-06/J-07 were withheld for a
documented operational-safety reason, not left unknown — each was still answered via direct,
independently-verified source-code citation instead of a live render. See the safety note at the
top of this report.)

---

## Supporting probe evidence

### `GET /research/datasets` latency (J-02 support; safe, bounded, explicitly sanctioned by the
iteration spec's verification actions — does not touch the dangerous edge-report path)

```
HTTP:200 TIME:30.129467s SIZE:8588 bytes
dataset_count: 18
integrity_errors: []
```

Matches `docs/goal.md`'s cited "31.4s to return 8.6KB" almost exactly, freshly reproduced.

### `GET /research/setups` latency (J-06 support; same safety class as the datasets probe —
bounded/deterministic, unlike the open-ended edge-report sweep)

```
HTTP:200 TIME:268.947424s SIZE:4497772 bytes
```

**4 min 29s** to return ~4.5MB of setups/case-study data on the real corpus (18 datasets) — a
finite, deterministic (if slow) cold scan, matching `docs/goal.md`'s documented "minutes when
cold" figure. Confirms J-06's baseline: no durable scan cache exists yet, so every request pays
the full O(n²) scan + re-hash cost; only a restart-wiped in-process `_SCAN_CACHE` slot exists
(code citation above). This probe is supplementary context for J-06, not load-bearing for its
FAIL verdict (which rests on the direct code citation above).

---

## Golden replay scripts written this iteration

- `runs/goal-session-fast_wall/journey-scripts/J-07.json` — covers the sim-cockpit
  (SIM-BUYER→buyer_control, SIM-SELLER→seller_control), `/journal`, `/studies`, `/performance`
  legs of J-07 that were actually live-verified this run. Linted clean
  (`demo_runner.py --mode lint`). `/structure` intentionally excluded (not exercised live this
  iteration).
- No scripts written for J-01–J-06 (all verified FAIL/absent — nothing exists yet to replay).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (real corpus: `.data/datasets`, 882MB, 18 datasets, 0
  integrity errors)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-17
- **Backend suite:** 1392 passed, 7 skipped, 0 failed (433.05s)
- **config_fingerprint:** `4d665603569b9dbf` (confirmed, matches frozen value)
- **`git diff --stat apps/`:** empty throughout (zero source changes this iteration)
- **Evidence directory:** `reports/qa/goal-fast_wall-iter-0-evidence/`
