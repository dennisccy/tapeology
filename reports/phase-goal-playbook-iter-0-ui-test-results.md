# Goal Iteration goal-playbook-iter-0 — UI Test Results

**Phase:** goal-playbook-iter-0
**Date:** 2026-08-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- This is a BASELINE assessment iteration (Mode: baseline, iter-0 of session `playbook`, Era
     B2 "The Playbook"). Per docs/phases/goal-playbook-iter-0.md, J-01 through J-09 are EXPECTED
     to FAIL (none of the playbook era's capabilities have been built yet — zero code changes
     this iteration, confirmed via `git diff --stat ed87dca -- apps/` = empty and
     `git status --short -- apps/` = empty) and J-10 (the kept-product regression sentinel) is
     EXPECTED to PASS on its KEPT-behavior evidence. The verdict above tracks J-10 — the one
     journey that gates "does the already-shipped product still work" — which passed with strong,
     fully browser-verified evidence across all three kept routes plus a clean full-suite run.
     J-01–J-09 FAILing is the correct, desired baseline recording, not a QA or pipeline
     malfunction: this exactly mirrors the precedent set by Era B's own baseline iteration
     (`docs/phases/goal-desk-iter-0.md` / `reports/phase-goal-desk-iter-0-ui-test-results.md`),
     which gave its analogous J-07 the same PASS-tracks-the-sentinel treatment. J-01–J-09 are
     scored P2 (baseline-probe; a not-yet-built future capability cannot fail the "kept product"
     gate); J-10 is P1 (the actual regression risk this iteration could have exposed). See
     "Baseline Context" below. -->

**Overall:** 1/10 journeys PASS (J-10, kept-behavior evidence — full era acceptance for J-10
itself, e.g. "MCP = exactly 20 tools," is not yet satisfiable and is explicitly not scored as a
failure per the iteration spec), 9/10 journeys FAIL as expected for a pre-build baseline
(J-01–J-09), 0 SKIPPED — every journey received a fully evidenced verdict.

---

## Baseline Context

This is iteration 0 (`Mode: baseline`) of the brand-new `playbook` goal-mode session (Era B2 "The
Playbook") — a verify-only iteration with **zero source changes**. Confirmed this session:
`git diff --stat ed87dcac4a76f801b3d2d31c382e7e6d667f4057 -- apps/` returned empty, HEAD is
exactly the era-open commit `ed87dcac4a76f801b3d2d31c382e7e6d667f4057`, and
`git status --short -- apps/` returned empty (clean working tree for `apps/`). Its purpose is to
record which of J-01–J-10 already pass/fail against the current (post-Era-B, plus the ratified R-2
forward-test interlude, pre-playbook) codebase. Per the iteration spec: *"J-01 through J-09 are
expected to be recorded FAILING this iteration — this is the honest, expected baseline for a
not-yet-started era, not a defect."* All 10 results below match that prediction exactly, and every
backend-absence claim is backed by a live grep/curl/browser run this session (not copied from the
decomposer's decompose-time notes), including a conclusive whole-tree check:
`grep -rli "playbook" apps/backend/app/` and `grep -rli "playbook" apps/backend/tests/` both
returned **zero matches** — no playbook module, route, or fixture exists under any name, anywhere
in the backend; `apps/backend/.data/` lists no `playbook`-named store directory either.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | baseline-probe | P2 | With no record, `GET /research/desk/playbook` serves the honest empty payload; `desk_playbook_features.py`/`desk_playbook_detect.py`/`desk_playbook.py`, `PlaybookStore`, and the GET route exist | Browser-navigated to `http://localhost:8301/research/desk/playbook` → `{"detail":"Not Found"}` (HTTP 404, curl-cross-confirmed). Whole-tree grep `grep -rli "playbook" apps/backend/app/` and same over `apps/backend/tests/` → 0 matches. `desk_playbook_features.py`, `desk_playbook_detect.py`, `desk_playbook.py` all absent from `apps/backend/app/research/`. No `*playbook*` fixture under `apps/backend/tests/fixtures/` — feature not yet built | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-01-route-404.png` |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | baseline-probe | P2 | Measurement extension records forward/MDD/`invalidation_breached` per signal; `desk_playbook_compute.py` + `desk_playbook_log.py` exist; `GET /research/desk/playbook/runs` serves the run ledger | Browser-navigated to `http://localhost:8301/research/desk/playbook/runs` → `{"detail":"Not Found"}` (HTTP 404). `desk_playbook_compute.py` and `desk_playbook_log.py` both absent from `apps/backend/app/research/` — trivially blocked on J-01's absent store/detect modules, exactly as the iteration spec predicts | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-02-route-404.png` |
| UT-J-03 | The Playbook lands on `/desk` | smoke | P2 | A "Playbook Signals" section, session-date input, Run Playbook button, signals table, and provenance line render below the shipped `/desk` sections; every shipped section still renders exactly as before | Navigated to `http://localhost:3301/desk` (fresh `next dev` server, started 07:44, after every relevant source file's mtime — no stale-build risk). Every shipped section rendered: Screen History, Forward Returns, Run Screen/Top-up/Reconcile Index/Deep Backfill controls, Briefing (101 ranked rows), Skipped Members, Top-up Runs, Index Reconciliation, Screen Runs, Screen Comparison, Provenance. `document.body.innerHTML` case-insensitive scan for "playbook" (via `eval`, covering text AND `data-testid` attributes) → **0 occurrences** — no Playbook Signals section, no Run Playbook control, no playbook-prefixed `data-testid` anywhere. `grep -ic "playbook"` on `apps/frontend/app/desk/page.tsx` and `apps/frontend/lib/api.ts` → 0 matches each — feature not yet built | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | baseline-probe | P2 | JBE/DBI/cup-and-handle detectors fire on fixture sessions; at least one signal of each new setup legible in the J-03 section on the fixture rig | Same `/desk` page state as J-03 (0 "playbook" occurrences — structurally impossible for any JBE/DBI/cup-and-handle chip to render since no Playbook Signals section exists at all). Backend grep for `jump-base-explosion`, `drop-base-implosion`, and `cup-and-handle` (case-insensitive, separately) over `apps/backend/app/research/` → 0 matches for any — trivially blocked on J-01's absent shared `desk_playbook_detect.py` module | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` (shared with J-03) |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | baseline-probe | P2 | A capitulation signal + a marker-decorated signal legible on the fixture rig | Same `/desk` page state (0 "playbook" occurrences). Backend `grep -rlEi "capitulation" apps/backend/app/research/` → 0 matches — trivially blocked on J-01's absence | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` (shared with J-03) |
| UT-J-06 | The range family — range trades, double top/bottom | baseline-probe | P2 | One range signal and one double-top signal legible on the fixture rig | Same `/desk` page state (0 "playbook" occurrences). Backend grep for `double-top` and `double-bottom` (case-insensitive, separately) over `apps/backend/app/research/` → 0 matches for either — trivially blocked on J-01's absence | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` (shared with J-03) |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | baseline-probe | P2 | `GET .../backscan/plan` serves a metadata-only plan; `desk_playbook_backscan.py` exists; the `/desk` Backscan panel renders | Browser-navigated to `http://localhost:8301/research/desk/playbook/backscan/plan` → `{"detail":"Not Found"}` (HTTP 404). `desk_playbook_backscan.py` absent from `apps/backend/app/research/` — feature not yet built | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-07-route-404.png` |
| UT-J-08 | The evidence view — distributions beside the null, min-n honest | baseline-probe | P2 | `GET /research/desk/playbook/evidence` folds recorded records into distribution cells; `desk_playbook_evidence.py` exists; the `/desk` Playbook Evidence section renders | Browser-navigated to `http://localhost:8301/research/desk/playbook/evidence` → `{"detail":"Not Found"}` (HTTP 404). `desk_playbook_evidence.py` absent from `apps/backend/app/research/` — feature not yet built | FAIL (expected at baseline) | `reports/qa/goal-playbook-iter-0-evidence/J-08-route-404.png` |
| UT-J-09 | MCP contract v4 — 20 read-only tools | baseline-probe | P2 | MCP server advertises exactly 20 tools including `desk_playbook`/`desk_playbook_evidence` | Live MCP tool roster this session (the `mcp__tapeology__*` proxies actually available) enumerates exactly **18** tools: `backtests, bars, datasets, desk_forward, desk_screen, desk_universe, edge_report, get_endpoint, levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability, ui_route_map` — no `desk_playbook`/`desk_playbook_evidence`. `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple independently inspected: exactly 18 entries, the same names, ending in `get_endpoint` — matches the live roster exactly, and passed clean in the full suite run (Step below). Still the pre-playbook 18-tool contract | FAIL (expected at baseline) | none (non-browser MCP-protocol + source check; no web page exists to screenshot for a tool-roster count) |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | Full backend suite green at the era-open baseline count; `config_fingerprint` = `08e471b10130e1e2`; cockpit sim tape+chart, `/structure` pinned-AAPL Load, every shipped `/desk` section render as shipped; nav = exactly 3 routes. (J-10's own literal acceptance also names "MCP = exactly 20 tools" — not yet satisfiable until J-09 ships.) | Suite: **1926 passed, 8 skipped, 0 failed** in 165.71s, exit 0 — matches `docs/goal.md`'s cited era-open baseline (1926 pass / 8 skip) **exactly**, no drift. `Config().config_fingerprint()` = `08e471b10130e1e2`, confirmed live. **Cockpit:** typed `SIM-BUYER`, clicked Watch — Tape State settled **"Buyer Control"** (confidence 0.805 → 0.929 across two reads), `scenario: buyer_control` badge, live 10s logical candle + volume bars rendered and moved (bid ticked 100.18 → 100.74 between reads — confirmed live, not frozen despite headless mode), `Tape 10s/30s/60s` timeframe switch present, Quote/Features/Recent Trades/Observations/Event Log all populated; honest `"No recorded bars for SIM-BUYER"` / `"No tradable map for SIM-BUYER"` for the synthetic ticker (correct — no fabricated band/candle data for a symbol with no real market data). **`/structure`:** loaded `AAPL` as-of `2026-06-22T23:59:59Z` (query-param prefill confirmed: Symbol input `value="AAPL"`, As-of input `value="2026-06-22 19:59:59"`, both populated before any click) — clicked Load — Tradable Map rendered `resistance 300.11–302.2 Class A score 171 members 849 [round number]` (the cited "300–302" wall) plus 4 more resistance + 5 support bands, S/R band overlay drawn on the candle chart with the as-of marker, `CHART TIMEFRAME` selector (1m/5m/1h/4h/1d/1w) present. **`/desk`:** every shipped section rendered (Screen History, Forward Returns, Run Screen/Top-up/Reconcile/Deep Backfill, Briefing — 101 ranked rows, Skipped Members, Top-up Runs, Index Reconciliation, Screen Runs, Screen Comparison, Provenance) — same capture as J-03. `GET /meta/ui-routes` → exactly 3 route objects (Cockpit, Structure, Desk). MCP-count clause (20 tools) confirmed **not yet satisfiable** (18 today, per J-09) — recorded as pending per the iteration spec's explicit carve-out, not scored as a KEPT-product failure | **PASS** (kept-behavior evidence; the 20-tool-MCP clause of J-10's full acceptance is pending J-09, per the iteration spec) | `reports/qa/goal-playbook-iter-0-evidence/J-10-cockpit-sim.png`, `J-10-structure-aapl.png`, `J-03-desk-no-playbook.png` (shared, shipped-`/desk`-sections evidence) |

---

## Passed Tests

### UT-J-10 — The kept product stands — regression sentinel
**Verdict:** PASS (kept-behavior evidence; the "MCP = exactly 20 tools" clause of J-10's full
acceptance is correctly pending J-09, per the iteration spec — not scored as a failure)

**Evidence:**
- `reports/qa/goal-playbook-iter-0-evidence/J-10-cockpit-sim.png`
- `reports/qa/goal-playbook-iter-0-evidence/J-10-structure-aapl.png`
- `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` (shared — the same full-page
  `/desk` capture proves every shipped section renders, doubling as J-10's desk-kept-behavior
  evidence)

**Step 1 — full backend suite + fingerprint.** Ran
`apps/backend/.venv/bin/python -m pytest tests/ -v`: **"1926 passed, 8 skipped, 2 warnings"** in
165.71s, exit code 0. Matches `docs/goal.md`'s cited era-open baseline (1926 pass / 8 skip)
exactly — no drift. The two warnings are pre-existing library deprecation notices (`httpx` /
`websockets.legacy`), unrelated to this iteration. `python -c "from app.config import Config;
print(Config().config_fingerprint())"` (run from `apps/backend`) printed `08e471b10130e1e2`,
matching the pinned value.

**Step 2 — sim cockpit (`SIM-BUYER` → `buyer_control`, PriceChart capabilities).** Navigated to
`/`, mode was already `Simulated` (default, bold-highlighted). Typed `SIM-BUYER` into the `Ticker`
input (`aria-label="Ticker"`), clicked `Watch`: Tape State panel read **"Buyer Control"**
(confidence 0.805 at first capture, 0.929 moments later as the sim continued — genuinely live),
`scenario: buyer_control` badge present, event log read "Tape state changed to buyer_control" —
settlement confirmed. The `PRICE CHART` section showed live green/red 10s logical candle bars with
traded volume beneath, the `Tape 10s/30s/60s` timeframe-switch buttons visible and present. Bid
price moved from `100.18` to `100.74` between the initial text read and the later screenshot —
direct proof the tape was live-updating, not frozen (a known headless-Chrome
`visibilityState:"hidden"` risk noted in prior sessions; not triggered here). Quote (`Bid/Ask/
Spread/Last`), Features (Trade speed, Volume speed, Aggressive buy/sell ratio, Net aggressive
volume, Buy/Sell price impact, Average spread, Large prints, Absorption/Bid-refresh/Ask-refresh
scores), Recent Trades (15 rows, price/size/side), Observations (3 bullets), and Event Log all
populated correctly. For `SIM-BUYER` specifically, History correctly showed `"No recorded bars for
SIM-BUYER"` and the Tradable Map correctly showed `"No tradable map for SIM-BUYER"` — the honest,
correct behavior for a synthetic ticker with no real market data (no fabricated band/candle data).

**Step 3 — `/structure` Load for pinned AAPL `2026-06-22`.** Navigated to
`/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z`. Confirmed via DOM inspection (`eval`) that
the query params pre-filled the form BEFORE any click: Symbol input `value="AAPL"`, As-of input
(`data-testid="structure-as-of-input"`) `value="2026-06-22 19:59:59"`. Clicked
`Load` (`data-testid="structure-load-button"`); waited for real data. The Tradable Map rendered:
`resistance 300.11–302.2 Class A score 171 members 849 [round number]` — the cited "300–302" wall
— plus four more resistance bands (`308.63–310.79`, `298.02–300.1`, `310.8–312.97`,
`304.34–306.47`) and five support bands, on the candle chart with the S/R band overlay and the
`as-of` marker rendered. `CHART TIMEFRAME` selector (`1m 5m 1h 4h 1d 1w`) present. Registry
(Champion `v1`/`default`, all three strategies' parameter tables) and Comparison (founding-baseline
PnL-ledger numbers) sections also rendered correctly, read-only, as shipped.

**Step 4 — `/desk` shipped-section sweep.** Navigated to `/desk`. Full-page markdown/text
extraction confirmed every shipped section present and rendering real served content: Screen
History; Forward Returns (with the full signed-forward-cell / dual-MDD / baseline-comparison
copy); Run Screen / Top-up / Reconcile Index / Deep Backfill controls (with the current pins'
honest state: "No screen is recorded under the pins that resolve for today — a run would walk 101
members," "3939 window(s) over 101 member(s)..."); Briefing (101 ranked rows, paginated, symbol
links to `/structure?symbol=...&asof=...`); Skipped Members ("No members were skipped in this
screen"); Top-up Runs (latest run `topup-2026-08-09-7010a90f8d0f`, 101 pairs); Index Reconciliation
(latest run, "no drift" before/after); Screen Runs (latest run
`screenrun-2026-08-09-f363495c65c9`); Screen Comparison (`screen-2026-08-10-...` vs
`screen-2026-08-09-...`, "rows compared 101 · rank changed 0 · side changed 0"); Provenance (record
id, bar-store signature, pins-resolved-now state). No errors, no missing sections, no playbook
content anywhere (0 "playbook" occurrences confirmed via `eval` over `document.body.innerHTML`).

**Step 5 — nav route count.** `GET /meta/ui-routes` →
`{"routes":[{"path":"/","label":"Cockpit","nav":true},{"path":"/structure","label":"Structure","nav":true},{"path":"/desk","label":"Desk","nav":true}]}`
— exactly 3 route objects, matching the required nav.

**Step 6 — pending clause, explicitly not scored as a failure.** `EXPECTED_TOOLS` lists exactly 18
tools (not 20) — the one desk-completion clause of J-10's literal acceptance text that cannot be
satisfied until J-09 ships, per the iteration spec's explicit carve-out ("the MCP-count clause of
J-10's acceptance — 20 tools — is not yet satisfiable and should be noted as such, not scored as a
failure of the KEPT product"). Recorded here as pending, not as a regression of the kept product.

Golden replay script written: `runs/goal-session-playbook/journey-scripts/J-10.json` (covers the
Cockpit `SIM-BUYER` settling flow + the `/structure` AAPL `2026-06-22` Load flow, asserting the
`300.11` band text renders, + a `/desk` shipped-section sweep asserting the static `Forward
Returns` header). Linted clean (`demo_runner.py --mode lint --scripts-dir
runs/goal-session-playbook/journey-scripts --journeys J-10` → `J-10 ok`).

---

## Failed Tests

<!-- All nine of these are the EXPECTED, CORRECT baseline result for a pre-build iteration — see
     "Baseline Context" above. Each entry cites the exact route/grep/DOM evidence gathered THIS
     session, live, not copied from decompose-time notes. -->

### UT-J-01 — The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No playbook signal/detect/store subsystem exists yet.

**Evidence:**
- Browser-navigated to `http://localhost:8301/research/desk/playbook` → `{"detail":"Not Found"}`
  (HTTP 404)
- `grep -rli "playbook" apps/backend/app/` → no matches (whole app tree)
- `grep -rli "playbook" apps/backend/tests/` → no matches (whole tests tree, including fixtures)
- Individually confirmed absent: `apps/backend/app/research/desk_playbook_features.py`,
  `desk_playbook_detect.py`, `desk_playbook.py`
- `apps/backend/.data/` directory listing has no `playbook`-named store dir

**Expected:** With no record, `GET /research/desk/playbook` serves the honest empty payload; on
the fixture rig a run records golden signals byte-identically on re-run.
**Actual:** The route, primitives module, detect module, store module, and fixtures do not exist.
Confirmed absent, not partially built.

---

### UT-J-02 — Every signal measured — the rail's own conventions, anchored at the trigger bar
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No measurement extension or compute-manager trio exists yet.

**Evidence:**
- Browser-navigated to `http://localhost:8301/research/desk/playbook/runs` →
  `{"detail":"Not Found"}` (HTTP 404)
- Individually confirmed absent: `apps/backend/app/research/desk_playbook_compute.py`,
  `desk_playbook_log.py`

**Expected:** Fixture goldens assert exact horizon returns/MDD per signal; the run ledger records
one row per terminal run.
**Actual:** The route and both modules do not exist. Trivially blocked on J-01's own absence.
Confirmed absent.

---

### UT-J-03 — The Playbook lands on `/desk`
**Verdict:** FAIL (expected at baseline)
**Failure:** No Playbook Signals section, Run Playbook control, or playbook `data-testid` exists
on `/desk`; every shipped section is unaffected.

**Steps taken:**
1. Navigated Chrome to `http://localhost:3301/desk` (after confirming the `next dev` server
   serving `:3301` was started at 07:44 — after every relevant source file's last modification —
   so no stale-build risk per T-9; a full `rm -rf .next` rebuild was not additionally performed
   since `next dev` recompiles from live source on each request, and zero playbook code exists to
   bake in either way).
2. Extracted the rendered page as markdown — confirmed every shipped section heading present
   (Screen History, Forward Returns, Run Screen/Top-up/Reconcile/Deep Backfill, Briefing, Skipped
   Members, Top-up Runs, Index Reconciliation, Screen Runs, Screen Comparison, Provenance) and no
   "Playbook"/"Backscan" heading anywhere.
3. Ran `document.body.innerHTML.toLowerCase().match(/playbook/g)` via `eval` — result: 0
   occurrences (covers rendered text AND every DOM attribute including `data-testid`).
4. Cross-checked source: `grep -ic "playbook" apps/frontend/app/desk/page.tsx` → 0;
   `grep -ic "playbook" apps/frontend/lib/api.ts` → 0.

**Expected:** A session-date input, Run Playbook button (live progress + cancel), signals table,
honest empty state, and provenance line render below the shipped sections.
**Actual:** None of the above exist. Every shipped section renders exactly as before, with zero
playbook content anywhere in the DOM. Confirmed absent, not partially built.

**Evidence:** `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png`

---

### UT-J-04 — The continuation family — JBE, DBI, cup-and-handle
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No JBE/DBI/cup-and-handle detector implementation exists
anywhere; trivially blocked by J-01's absent shared detect module.

**Evidence:**
- Same `/desk` page state as J-03 (0 "playbook" occurrences) — structurally no section exists for
  any detector signal to render into
- `grep -rlEi "jump.base.explosion|drop.base.implosion|cup.and.handle" apps/backend/app/research/`
  → no matches

**Expected:** Fixture goldens for JBE, DBI, and cup-and-handle; at least one signal of each new
setup legible in the J-03 section.
**Actual:** No detector code exists anywhere in the codebase. Confirmed absent.

---

### UT-J-05 — The climax family — capitulation entry, euphoria marker
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No capitulation/euphoria-marker detector implementation exists
anywhere; trivially blocked by J-01's absence.

**Evidence:**
- Same `/desk` page state (0 "playbook" occurrences)
- `grep -rlEi "capitulation" apps/backend/app/research/` → no matches

**Expected:** A capitulation signal + a marker-decorated signal legible on the fixture rig.
**Actual:** No detector code exists anywhere. Confirmed absent.

---

### UT-J-06 — The range family — range trades, double top/bottom
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No range-trade/double-top/double-bottom detector implementation
exists anywhere; trivially blocked by J-01's absence.

**Evidence:**
- Same `/desk` page state (0 "playbook" occurrences)
- `grep -rlEi "double.top|double.bottom" apps/backend/app/research/` → no matches

**Expected:** One range signal and one double-top signal legible on the fixture rig.
**Actual:** No detector code exists anywhere. Confirmed absent.

---

### UT-J-07 — The back-scan — every recorded session, resumable and append-only
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No back-scan subsystem exists yet.

**Evidence:**
- Browser-navigated to `http://localhost:8301/research/desk/playbook/backscan/plan` →
  `{"detail":"Not Found"}` (HTTP 404)
- Individually confirmed absent: `apps/backend/app/research/desk_playbook_backscan.py`

**Expected:** `GET .../backscan/plan` serves a metadata-only plan; the `/desk` Backscan panel
renders a plan preview + trigger + runs table.
**Actual:** The route and module do not exist. Trivially blocked on J-01/J-02's absence. Confirmed
absent.

---

### UT-J-08 — The evidence view — distributions beside the null, min-n honest
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No evidence-projection subsystem exists yet.

**Evidence:**
- Browser-navigated to `http://localhost:8301/research/desk/playbook/evidence` →
  `{"detail":"Not Found"}` (HTTP 404)
- Individually confirmed absent: `apps/backend/app/research/desk_playbook_evidence.py`

**Expected:** `GET /research/desk/playbook/evidence` folds recorded records into per-(setup, side)
distribution cells beside the pooled baseline; the `/desk` Playbook Evidence section renders the
table.
**Actual:** The route and module do not exist. Trivially blocked on J-01/J-02's absence. Confirmed
absent.

---

### UT-J-09 — MCP contract v4 — 20 read-only tools
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** MCP surface still advertises the pre-playbook 18-tool contract.

**Evidence:**
- Live MCP tool roster this session (the `mcp__tapeology__*` proxies actually reachable):
  `backtests, bars, datasets, desk_forward, desk_screen, desk_universe, edge_report, get_endpoint,
  levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy,
  tradability, ui_route_map` — 18 entries, no `desk_playbook`/`desk_playbook_evidence`
- `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple: exactly the same 18 entries,
  ending in `get_endpoint` — independently confirmed via source read
- The MCP suite (`test_mcp_server.py`) passed clean inside the full backend suite run (Step 1 of
  UT-J-10), confirming the 18-tool contract holds under test, not just by inspection

**Expected:** 20 entries, including `desk_playbook` and `desk_playbook_evidence`.
**Actual:** 18 entries. Confirmed unchanged from the pre-playbook contract.

---

## Skipped Tests

None at the journey level — every one of J-01–J-10 received a fully evidenced PASS/FAIL verdict.
No Chrome MCP or frontend/backend availability issue occurred this run (frontend `:3301` and
backend `:8301` were both up throughout; Chrome attached cleanly to the pre-launched CDP endpoint
on `127.0.0.1:9222`, no port-9222 recovery was needed).

---

## Golden replay scripts written this iteration

- `runs/goal-session-playbook/journey-scripts/J-10.json` — covers the Cockpit `SIM-BUYER` →
  watching flow, the `/structure` AAPL `2026-06-22` Load flow (asserts the `300.11` band text
  renders), and a `/desk` shipped-section sweep (asserts the static `Forward Returns` header).
  Linted clean (`demo_runner.py --mode lint --scripts-dir runs/goal-session-playbook/journey-scripts
  --journeys J-10` → `J-10 ok`).
- No scripts written for J-01–J-09 (all verified FAIL/absent — nothing exists yet to replay; a
  golden script is only useful for guarding an already-passing behavior, per the agent
  instructions' best-effort rule).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to
  the pre-launched CDP endpoint on `127.0.0.1:9222` (headless throughout — never switched to
  headed mode, never re-profiled)
- **Test Date:** 2026-08-10
- **Backend suite:** 1926 passed, 8 skipped, 0 failed (165.71s, exit 0) — matches `docs/goal.md`'s
  cited era-open baseline (1926 pass / 8 skip) exactly
- **config_fingerprint:** `08e471b10130e1e2` (confirmed live, matches the frozen pin)
- **`git diff --stat ed87dca -- apps/`:** empty throughout (zero source changes this iteration)
- **`git status --short -- apps/`:** empty (clean working tree)
- **Evidence directory:** `reports/qa/goal-playbook-iter-0-evidence/`
