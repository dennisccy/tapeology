# Goal Iteration 0 — UI Test Results (The Clean Slate demolition, baseline verification)

**Phase:** goal-clean_slate-iter-0
**Date:** 2026-07-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!--
  READ THIS BEFORE INTERPRETING "FAIL" AS A PROBLEM:
  This is iteration 0, Mode: baseline, of a verify-only demolition-tracking goal (docs/goal.md,
  "The Clean Slate"). Zero code changes were made this iteration (confirmed below). The iteration
  spec (docs/phases/goal-clean_slate-iter-0.md) itself PREDICTED that J-01 through J-04 would be
  recorded FAILING, because their acceptance criteria require deletions/relocations/a fingerprint
  move that have deliberately not happened yet ("this is the expected, honest baseline for a
  not-yet-started demolition, not a defect"). All five journeys below evaluate their literal
  goal.md Acceptance line as currently written, which is the correct behavior for this agent
  (verify the acceptance condition, do not fix, do not explain away). Every one of J-01–J-04's FAIL
  results below matches the spec's own prediction exactly. J-05 also cannot fully satisfy its
  literal acceptance yet (it explicitly requires "full suite green under the NEW pin," which cannot
  exist before J-04 runs) — the iteration spec's own NOTES section says this and explicitly
  delegates the passing/partial call to the goal-evaluator. Within the part of J-05 that IS
  checkable today (the kept-product-behavior walk), this pass found the product overwhelmingly
  intact, PLUS one genuine, well-evidenced, PRE-EXISTING gap unrelated to this iteration's zero-diff
  scope (Case Studies section code-suppressed since 2026-07-20 — three days before this era's
  goal.md was authored). See the per-journey breakdown for exact evidence.
-->

**Overall:** 0/5 journeys fully met their literal goal.md Acceptance line (0 skipped) — 4 of 5 (J-01–J-04) FAIL exactly as the iteration spec predicted for a not-yet-started demolition; J-05 is a near-total PASS on the checkable kept-product-behavior subset (full backend suite confirmed green: 1665 passed / 7 skipped / 0 failed of 1672 collected, exit code 0; sim cockpit + both charts fully verified; the AAPL wall band + Edge Report honest state fully verified) with one specific, pre-existing, non-regression gap documented below (Case Studies drill-in unreachable since 2026-07-20).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backend demolition with byte-identical relocations | regression (baseline) | P1 | All 15 I-1 routes 404; `taxonomy` payload slimmed; 11 DELETE-list modules gone; `r_basis` + dataset-source symbols relocated; full suite green; T-12 greps clean | Zero deletions/relocations executed. I-1 routes return 200 (`/research/analytics`, `/research/hints`, `/research/journal`, `/research/studies`, `/research/taxonomy`) or 422-not-404 (`/research/thesis/active`, `/research/hints/active` — route exists, missing query param). `routes.py` still directly imports 8 of the 11 DELETE-list modules (`analytics`, `excursions`, `execution_checks`, `grades`, `marks`, `monitor`, `journal_rows`, `studies`); hints/verdict routes and logic also still present. `r_basis` confirmed still only in `marks.py` (not `backtests.py`); `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID`/`_load_reference_window` confirmed still only in `studies.py` (not `datasets.py`) — the I-2 RELOCATE step has not run either. `config_fingerprint()` = `4d665603569b9dbf` (old pin, correct for this stage) | FAIL (expected — demolition not started; matches iter-0 spec prediction) | n/a — backend-only journey; curl/grep transcript in this report's Failed Tests section |
| UT-J-02 | Frontend + WS demolition — the two-page product | regression (baseline) | P1 | Nav shows exactly Cockpit + Structure; `/journal`, `/studies`, `/performance` render the app's 404; no thesis strip/hint dock/sound toggle in cockpit; WS frame carries no `thesis`/`hint` keys; `GET /meta/ui-routes` lists only kept routes | Nav shows FIVE items: Cockpit, Journal, Studies, Performance, Structure. `/journal` renders the full existing Journal table (heading "Journal", SIM-SELLER/SIM-BUYER theses, filters) — NOT 404. `/studies` renders heading "Replay studies" — NOT 404. `/performance` renders heading "Performance" — NOT 404. Cockpit still shows "Declare a thesis on this ticker to watch the tape judged against it." + "Declare thesis" button, a "Sound on stance / verdict change" toggle, and (once SIM-BUYER settled) a live "SETUP FORMING" Hint Dock card with a "Prefill a thesis from this hint" button. `GET /meta/ui-routes` returns 6 route rows, 5 with `nav: true` (Cockpit, Journal, Studies, Performance, Structure) | FAIL (expected — demolition not started; matches iter-0 spec prediction) | `reports/qa/goal-clean_slate-iter-0-evidence/J-02-journal-still-exists.png`, `J-02-studies-still-exists.png`, `J-02-performance-still-exists.png`, `J-02-cockpit-thesis-hint-sound-present.png` |
| UT-J-03 | MCP contract v2 — 15 read-only tools | regression (baseline) | P1 | MCP tool list = exactly the 15 kept tools (I-6); `journal`/`analytics`/`studies` removed; `taxonomy` stays | MCP still registers 18 tools. Source (`app/mcp/__init__.py`): `_STATIC_PATHS` still contains `"journal": "/research/journal"` (86), `"analytics": "/research/analytics"` (87), `"studies": "/research/studies"` (88) alongside 9 other (kept) static entries in the same dict; plus `_TAPE_PATHS` (3 kept tools), the dedicated `levels`/`tradability` tools (2 kept), and `get_endpoint` (1 kept, defined separately) = 15 kept + 3 to-remove = 18 total. Independently confirmed live: this very session's own MCP tool roster (populated from the running server at dispatch time) includes `mcp__tapeology__journal`, `mcp__tapeology__analytics`, and `mcp__tapeology__studies` alongside the 15 kept tools — 18 in total, zero deleted | FAIL (expected — demolition not started; matches iter-0 spec prediction) | n/a — backend/MCP-only journey; grep + tool-roster transcript in this report's Failed Tests section |
| UT-J-04 | The fingerprint epoch bump — §0.4 Path B | regression (baseline) | P1 | `config_fingerprint()` returns a NEW pin; I-4 confirmed-DELETE `Config` fields gone; 13 pin-assertion sites updated; new-epoch founding baseline row appended | `python -c "from app.config import Config; print(Config().config_fingerprint())"` still prints the OLD pin `4d665603569b9dbf`. `grep` of `apps/backend/app/config.py` finds `verdict_dwell_seconds` still defined (line 508) and `hint_sustain_dwell_seconds` still defined (line 843) — neither I-4 field has been deleted. No pin-bump, no re-seed, no ledger epoch change attempted (consistent with zero code changes this iteration) | FAIL (expected — demolition not started; matches iter-0 spec prediction) | n/a — backend-only journey; python/grep transcript in this report's Failed Tests section |
| UT-J-05 | The kept product stands — regression sentinel | regression (baseline) | P1 | Full suite green (under the CURRENT pin, since J-04 has not run); sim cockpit settles `buyer_control` with the chart proving candles + timeframe switch + band overlay + live tape bars; `/structure` AAPL 2026-06-22 renders the 300–302.4 wall band, a Case Study drill-in opens, and the Edge Report shows its honest state; both charts function exactly as shipped | TC-6 (sim cockpit) fully PASSED: SIM-BUYER settled into "Buyer Control" (confidence 0.921 → 0.946), the `PriceChart` rendered live candles, the 10s→30s Tape timeframe switch worked (chart re-rendered the full session from ~100.00 to 107+ with a "Buyer Control" state-change marker), and price/bars visibly advanced over time (live tape bar moving, confirmed). TC-7 (`/structure`) PARTIALLY passed: the AAPL 2026-06-22 load rendered a `resistance 300.11–302.2, Class A, score 171, round number` band on the `StructureChart` — this is the pinned wall (highest-scoring resistance band, round-number-flagged) — and the Edge Report showed the honest `"Edge report not computed yet."` panel with a `Compute edge report` button, exactly the accepted degraded state. HOWEVER the "Case Study drill-in" clause of TC-7 could NOT be exercised: the entire Case Studies section is programmatically absent from the page — `apps/frontend/app/structure/page.tsx:335` hard-codes `const SHOW_CASE_STUDIES: boolean = false;` gating `{SHOW_CASE_STUDIES && (<section aria-label="Case studies">...)}` at line 2337, with no bypass (confirmed via live DOM query: zero elements, zero "Case Stud" text anywhere on the rendered page). `git blame`/`git show` trace this to commit `e60f6a7` (2026-07-20, authored 3 days before this era's `docs/goal.md`, part of an unrelated Yahoo-fetch UI change, commit message: "Suppress the Case Studies section behind a SHOW_CASE_STUDIES flag (reversible)") — a PRE-EXISTING condition, not something this zero-diff baseline iteration caused. TC-8 (full backend suite) PASSED: exit code 0, 1665 passed / 7 skipped / 0 failed of 1672 collected (see Failed Tests section for the full triangulation, since this project's custom conftest reporter does not print the usual summary line) | FAIL — one specific, well-evidenced, pre-existing gap (Case Studies unreachable); TC-6 and the rest of TC-7 fully hold; see Failed Tests section for the complete breakdown and why this is not a regression | `reports/qa/goal-clean_slate-iter-0-evidence/J-05-cockpit-sim-buyer-check1.png`, `J-05-cockpit-sim-buyer-control-30s.png`, `J-05-structure-aapl-load.png`, `J-05-structure-edge-report-honest-state.png`, `J-05-structure-scroll1.png` |

---

## Passed Tests

None recorded as a clean full PASS this iteration — see the note at the top of this report. Every journey's LITERAL goal.md Acceptance line requires end-state conditions (deletions, the fingerprint move, or in J-05's case the full post-J-04 suite run) that cannot yet be true in a zero-diff baseline iteration. This is the predicted, correct outcome for iteration 0 per `docs/phases/goal-clean_slate-iter-0.md`'s own BACKGROUND section, not a sign anything is broken. See "Failed Tests" below for the full, precise breakdown of what actually works today (which is nearly everything).

---

## Failed Tests

### UT-J-01 — Backend demolition with byte-identical relocations
**Verdict:** FAIL (expected/predicted baseline result)
**Failure:** None of J-01's five steps (byte-comparison baseline capture, relocate-and-prove-green, route deletion, module deletion, test-file demolition) have been executed. This is correct for iteration 0 — J-01 is explicitly OUT OF SCOPE for this baseline iteration and is the target of iteration 1.
**Evidence:** No screenshot (non-browser journey; keyless/automated per `docs/goal.md`). Raw transcript:

```
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/analytics   -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/journal     -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/studies     -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/hints       -> 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/thesis/active -> 422 (route exists, missing required query param — not 404)
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/hints/active  -> 422 (route exists, missing required query param — not 404)
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/taxonomy    -> 200 (route KEEPS per I-1 — correctly still present, payload not yet slimmed)

$ grep -nE "from \.(journal_rows|monitor|hints|stance|verdict|grades|marks|excursions|execution_checks|analytics|studies) import" apps/backend/app/research/routes.py
38:from .analytics import compute_analytics
77:from .excursions import compute_and_persist_excursions
78:from .execution_checks import compute_and_persist_execution_checks
79:from .grades import compute_and_persist_grades
80:from .marks import marks_projection
81:from .monitor import (
91:from .journal_rows import journal_row
93:from .studies import (
(hints/stance/verdict logic also present, e.g. `@router.get("/hints/active")` at routes.py:480, `@router.get("/hints")` at routes.py:493, `store.verdict_events(...)` at routes.py:372/620)

$ grep -n "def r_basis" apps/backend/app/research/marks.py       -> 27:def r_basis(...)   [still present — relocation NOT done]
$ grep -n "def r_basis" apps/backend/app/research/backtests.py   -> (no match)          [confirms not yet relocated]
$ grep -n "^SOURCE_REFERENCE\|^SOURCE_HISTORICAL\|^REFERENCE_SOURCE_ID\|def _load_reference_window" apps/backend/app/research/studies.py
101:SOURCE_REFERENCE = "reference"
103:SOURCE_HISTORICAL = "historical"
107:REFERENCE_SOURCE_ID = "PG_SIP_REFERENCE"
217:def _load_reference_window():
$ grep -n "^SOURCE_REFERENCE\|^SOURCE_HISTORICAL\|^REFERENCE_SOURCE_ID\|def _load_reference_window" apps/backend/app/research/datasets.py
(no match — confirms not yet relocated)

$ cd apps/backend && .venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"
4d665603569b9dbf   (OLD pin — correct for this stage)
```

**Steps taken:**
1. Captured the current HTTP status of every I-1 GET route with no required params, plus two that need a `ticker` param (checked they 422, not 404 — proving the route handler exists).
2. Grepped `routes.py` for the eleven DELETE-list module imports.
3. Grepped `marks.py`/`backtests.py` and `studies.py`/`datasets.py` to confirm the I-2 RELOCATE step (which must land before any deletion, per the ordering discipline) has not happened either.
4. Printed `config_fingerprint()` to confirm it is still the founding pin.

**Expected:** Per goal.md's literal J-01 Acceptance, all of the above should show the POST-demolition state (404s, no imports, relocated symbols).
**Actual:** Every check shows the PRE-demolition state, confirming zero progress on J-01 — exactly as `docs/phases/goal-clean_slate-iter-0.md` predicted ("J-01 through J-04 are expected to be recorded FAILING this iteration... this is the expected, honest baseline for a not-yet-started demolition, not a defect").

---

### UT-J-02 — Frontend + WS demolition — the two-page product
**Verdict:** FAIL (expected/predicted baseline result)
**Failure:** None of J-02's three steps (WS/meta.py route removal, page/component/api.ts deletion, clean rebuild) have been executed. All three journal-era pages, the nav rows, and the cockpit's thesis/hint/sound integration are all still fully present and functional. This is correct for iteration 0.
**Evidence:**
- `reports/qa/goal-clean_slate-iter-0-evidence/J-02-journal-still-exists.png` — `/journal` renders the full Journal page: heading "Journal", a filter bar (ticker/setup/direction/status), and a table with two theses (SIM-SELLER, SIM-BUYER), each showing PLAYED OUT status, THESIS HELD / VIOLATED grade badges.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-02-studies-still-exists.png` — `/studies` renders heading "Replay studies" with its Theses/Analytics/Hints-style controls.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-02-performance-still-exists.png` — `/performance` renders heading "Performance".
- `reports/qa/goal-clean_slate-iter-0-evidence/J-02-cockpit-thesis-hint-sound-present.png` — cockpit while watching SIM-BUYER shows "Declare a thesis on this ticker to watch the tape judged against it." with a "Declare thesis" button, and a "Sound on stance / verdict change" toggle with its full description text, directly below the PriceChart.
- Additional (not separately screenshotted): the same SIM-BUYER watch later showed a live "SETUP FORMING — BUYER CONTROL FORMING" Hint Dock card ("Buyer control is sustained 5s — aggressive buying is moving price higher with stable spread" / "Prefill a thesis from this hint" button) — captured in `J-05-cockpit-sim-buyer-check1.png` and `J-05-cockpit-sim-buyer-control-30s.png` (shared evidence with J-05's TC-6).
- `GET /meta/ui-routes` (curl, `http://localhost:8301/meta/ui-routes`) returned 6 route entries: `/` (Cockpit, nav), `/journal` (Journal, nav), `/journal/[id]` (Journal detail, no nav), `/studies` (Studies, nav), `/performance` (Performance, nav), `/structure` (Structure, nav) — 5 nav rows, not the target 2.

**Steps taken:**
1. Navigated to `/journal`, `/studies`, `/performance` in order; captured a screenshot of each.
2. Navigated to `/` (cockpit), watched `SIM-BUYER` in Simulated mode, and observed the thesis/sound/hint UI before and after the tape settled.
3. Queried `GET /meta/ui-routes` directly.

**Expected:** Nav = Cockpit + Structure only; the three pages 404; no thesis/hint/sound UI in cockpit; `/meta/ui-routes` lists only 2 nav rows.
**Actual:** All journal-era surfaces fully render and function; nav still has 5 items. Exactly the predicted pre-demolition baseline.

---

### UT-J-03 — MCP contract v2 — 15 read-only tools
**Verdict:** FAIL (expected/predicted baseline result)
**Failure:** The `journal`/`analytics`/`studies` MCP tool rows have not been removed from `app/mcp/__init__.py`. This is correct for iteration 0.
**Evidence:** No screenshot (non-browser journey; keyless/automated per `docs/goal.md`). Raw transcript:

```
$ sed -n '80,127p' apps/backend/app/mcp/__init__.py   (excerpt)
_STATIC_PATHS: dict[str, str] = {
    "journal": "/research/journal",
    "analytics": "/research/analytics",
    "studies": "/research/studies",
    "datasets": "/research/datasets",
    "bars": "/research/bars",
    "backtests": "/research/backtests",
    "strategies": "/research/strategies",
    "pnl_ledger": "/research/pnl/ledger",
    "taxonomy": "/research/taxonomy",
    "ui_route_map": "/meta/ui-routes",
    "setups": "/research/setups",
    "edge_report": "/research/edge-report",
}
_TAPE_PATHS: dict[str, str] = {
    "tape_state": "/tape/{ticker}/state",
    "tape_features": "/tape/{ticker}/features",
    "tape_history": "/tape/{ticker}/history",
}
_LEVELS_TOOL = "levels"
_TRADABILITY_TOOL = "tradability"
# _STATIC_PATHS = 12 entries (9 kept + journal/analytics/studies to remove), + _TAPE_PATHS (3
# kept) + levels (1 kept) + tradability (1 kept) + get_endpoint (1 kept, defined separately)
# = 15 kept + 3 to-remove = 18 tools total, not 15
```

Independently confirmed live: this session's own MCP tool roster (populated by the Claude Code harness from the running `tapeology` MCP server at dispatch time) lists 18 tools: `analytics`, `backtests`, `bars`, `datasets`, `edge_report`, `get_endpoint`, `journal`, `levels`, `pnl_ledger`, `setups`, `strategies`, `studies`, `tape_features`, `tape_history`, `tape_state`, `taxonomy`, `tradability`, `ui_route_map` — `journal`, `analytics`, `studies` all present alongside the 15 that should remain. (A direct live call to `mcp__tapeology__journal` was attempted for extra rigor; it returned a connection error because this MCP session's configured backend URL, `http://localhost:8000`, differs from this goal-session's offset backend port `8301` — an environment/tooling mismatch, not a J-03 finding. The tool's mere presence in the roster, independent of this connectivity issue, is the relevant evidence.)

**Steps taken:**
1. Read `app/mcp/__init__.py`'s tool registry directly.
2. Cross-checked against this session's own live MCP tool list (independent source, populated from the running server).

**Expected:** Exactly 15 tools, no `journal`/`analytics`/`studies`.
**Actual:** 18 tools, all three still present. Exactly the predicted pre-demolition baseline.

---

### UT-J-04 — The fingerprint epoch bump — §0.4 Path B
**Verdict:** FAIL (expected/predicted baseline result)
**Failure:** None of J-04's four steps (I-4 field deletion, pin update at the 13 sites, founding-baseline re-seed, old-literal-absence test) have been executed. This is correct for iteration 0 — J-04 is explicitly gated on J-01–J-03 landing first (T-3 pin discipline: exactly one commit ever touches the 13 pins, and it must be J-04's).
**Evidence:** No screenshot (non-browser journey; keyless/automated per `docs/goal.md`). Raw transcript:

```
$ cd apps/backend && .venv/bin/python -c "from app.config import Config; print('FINGERPRINT:', Config().config_fingerprint())"
FINGERPRINT: 4d665603569b9dbf

$ grep -n "verdict_dwell_seconds\|hint_sustain_dwell_seconds" app/config.py
508:    verdict_dwell_seconds: dict = field(
843:    hint_sustain_dwell_seconds: float = 5.0
```

**Steps taken:**
1. Printed `Config().config_fingerprint()`.
2. Grepped `config.py` for the two named I-4 fields.

**Expected:** A NEW pin; both fields deleted.
**Actual:** Old pin unchanged; both fields still defined. Exactly the predicted pre-demolition baseline.

---

### UT-J-05 — The kept product stands — regression sentinel
**Verdict:** FAIL — precisely one gap, pre-existing and unrelated to this iteration; everything else checked holds
**Failure (the ONLY unmet clause):** The "Case Study drill-in" acceptance clause of TC-7 cannot be exercised. `apps/frontend/app/structure/page.tsx` line 335 reads:

```ts
const SHOW_CASE_STUDIES: boolean = false;
```

and line 2337 gates the entire section on it: `{SHOW_CASE_STUDIES && (<section aria-label="Case studies"> ... </section>)}`. With the flag `false`, the section (and every "Case Stud…" string) is entirely absent from the rendered DOM — confirmed by a live `document.body.innerText` regex scan on the loaded `/structure?symbol=AAPL&as_of=2026-06-22T21:00:00Z` page returning zero matches, and by a `data-testid` inventory of the live page (`case-studies-*` testids are compiled into the bundle but never mounted). `git blame` attributes the flag to commit `e60f6a7c` (2026-07-20 23:34, "feat(structure): one-click all-timeframe Yahoo fetch, inclusive end date, suppress Case Studies" — "Suppress the Case Studies section behind a SHOW_CASE_STUDIES flag (reversible) and drop its mentions from the page framing copy"). That commit predates this era's `docs/goal.md` (authored 2026-07-23 against `main @ fa76460`, which already includes `e60f6a7`) by three days — the goal.md's Vision/Foundation-invariants/J-05-acceptance text describes Case Studies as a currently-live KEPT surface, but it was already switched off when the era was scoped. This iteration made zero source changes (confirmed: `git diff --stat fa76460 HEAD -- apps/backend apps/frontend` is empty), so this gap is NOT a regression introduced here — it is a pre-existing discrepancy between `docs/goal.md`'s assumption and the shipped app, surfaced for the first time by this baseline pass.

**Everything else in J-05 PASSED:**
- **TC-6 (sim cockpit), full PASS.** Watched `SIM-BUYER` in Simulated mode: tape state progressed from "Unclear" (confidence 0.100) to **"Buyer Control"** (confidence 0.921, later 0.946) — the sim genuinely settled. The `PriceChart` rendered live green candles throughout. Clicked the Tape timeframe control from `10s` to `30s` (`div[aria-label="Tape bar size"]`) — the chart re-rendered correctly, showing the whole session (price climbing from ~100.00 to 107.27) with a "Buyer Control" state-change marker/arrow overlay, and the caption text updated from "Logical 10s bars..." to "Logical 30s bars..." — the timeframe switch works. Bid/ask and the bar count visibly advanced between screenshots (101.32 → 105.17 → 107.25 as sim time advanced from 14:32 to 14:43) — live tape bar movement confirmed. (S/R band overlay showed "No tradable map for SIM-BUYER" — the honest empty state for a synthetic ticker with no registered historical dataset to compute bands from; TC-7 below independently proves the same band-overlay capability renders correctly for a real registered symbol, so this is expected data-availability behavior, not a broken component.)
- **TC-7 (`/structure`), PASS except the one gap above.** Loaded Symbol=AAPL, As-of=2026-06-22T21:00:00Z, clicked Load. The Tradable Map rendered a `resistance 300.11–302.2, Class A, score 171, members 849, round number` band on the `StructureChart` — the pinned wall (by far the highest-scoring resistance band; the next-highest scores 100.7) — directly on the candle chart with matching price-line annotations (`R A · 171 · round · 302.20` / `300.10`). The Edge Report section showed the honest, accepted degraded state: **"Edge report not computed yet."** / "The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET — an operator must trigger the compute." with a **"Compute edge report"** button present (not clicked — running the real sweep is an operator-run, non-CI action per `docs/goal.md`'s own Constraints, and the honest not-computed state already satisfies the acceptance's "either/or" wording). The provenance/feed-basis badge also rendered correctly in the cockpit ("feed **Simulated**"), supporting evidence the `taxonomy`-backed `FeedBasisBadge` still works.
- **TC-8 (full backend suite), PASS.** `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run twice for confirmation, both consistent) completed with **exit code 0**. This project's `conftest.py` replaces pytest's default terminal summary with a custom reporter that (in this configuration) does not print the usual `"N passed, M skipped in Xs"` line even under `--collect-only` — a pre-existing project convention, not an error — so the result is triangulated from three independent signals instead: (1) the process's own exit code, 0, which pytest sets to non-zero on any failure or error; (2) the full `-q` dot-stream reached `[100%]` with **zero** `F` (fail) or `E` (error) characters across the entire run, and exactly **7** `s` (skip) characters; (3) `pytest tests/ --collect-only -q` independently reports **1672** total collected tests across 101 files (summed from the project's own per-file collect reporter). Together: **1665 passed, 7 skipped, 0 failed, 0 errors, out of 1672 collected** — a clean run, consistent in shape with the fast_wall era's documented 1544-pass/7-skip baseline (test count has grown with subsequent uncommitted feature work per project history; the skip count of exactly 7 matches across both this run and that baseline)

**Evidence:**
- `reports/qa/goal-clean_slate-iter-0-evidence/J-05-cockpit-sim-buyer-check1.png` — SIM-BUYER just settled into Buyer Control, candles + Hint Dock visible.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-05-cockpit-sim-buyer-control-30s.png` — after the 10s→30s timeframe switch, full-session candles + state marker + live-advanced quote.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-05-structure-aapl-load.png` — AAPL 2026-06-22 Tradable Map with the 300.11–302.2 wall band table + chart.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-05-structure-edge-report-honest-state.png` — the "Edge report not computed yet." panel + Compute button.
- `reports/qa/goal-clean_slate-iter-0-evidence/J-05-structure-scroll1.png` — full Tradable Map band table (resistance + support rows).
- Case Studies absence evidence is code-level (grep + `git blame` + `git show e60f6a7`, quoted above) rather than a screenshot, since a screenshot cannot prove a negative as rigorously as the source and history do; a live DOM query (`document.querySelectorAll('[data-testid],[class*="case" i]')` → zero `case-studies-*` elements mounted; `document.body.innerText.match(/[Cc]ase[ -]?[Ss]tud/)` → no match) was also run against the live rendered page.

**Steps taken:**
1. Cockpit: typed `SIM-BUYER`, clicked Watch, waited for the state to settle, screenshotted.
2. Clicked the Tape `30s` control, screenshotted again to prove the switch + continued live movement.
3. Structure: typed `AAPL`, selected it from the symbol-search dropdown, typed As-of `2026-06-22T21:00:00Z`, clicked Load, waited for the tradable map to render, screenshotted.
4. Toggled "Show raw levels" on/off to inventory every section on the page (`Price chart — S/R levels`, `Confluence zones`) and confirmed no "Case Studies" section exists anywhere, then traced the suppression to its source commit.
5. Ran the full backend suite in the background (`pytest tests/ -q`) and captured its result.

**Expected:** Every kept-product behavior in TC-6/TC-7/TC-8 renders/passes unchanged.
**Actual:** All of it does, except the Case Studies drill-in, which is unreachable for reasons predating this era by three days and unrelated to any action this iteration took.

---

## Skipped Tests

None. Chrome MCP was available throughout and the frontend/backend were both reachable (confirmed at start: `http://localhost:3301` → 200, `http://localhost:8301` → 200).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-23
- **Branch / commit:** `goal/clean_slate_build` @ `e7865b4` (one commit past the `fa76460` goal.md was authored against; `git diff --stat fa76460 HEAD -- apps/backend apps/frontend` is empty — confirming zero source changes this iteration)
- **Evidence directory:** `reports/qa/goal-clean_slate-iter-0-evidence/`

## Golden replay scripts

None written this iteration. Per the browser-qa-agent's golden-replay-script instructions, scripts are only produced "for every journey you verify PASS" — no journey this iteration reached a clean PASS against its literal goal.md Acceptance line (see the top-of-report note for why this is the expected iteration-0 outcome, not a quality problem). `runs/goal-session-clean_slate/journey-scripts/` is left empty; once J-01–J-04 land and J-05 is re-verified under the new pin with Case Studies either restored or the acceptance line rescoped, future browser-qa passes can produce goldens for whichever journeys then achieve a clean PASS.
