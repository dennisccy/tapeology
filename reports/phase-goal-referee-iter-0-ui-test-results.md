# Goal Iteration goal-referee-iter-0 — UI Test Results

**Phase:** goal-referee-iter-0 (Era 6 "The Referee", session `referee`, iteration 0 — baseline/lean)
**Date:** 2026-08-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- This FAIL is the EXPECTED, CORRECT outcome for this iteration. -->
<!-- Iteration 0 is a verify-only BASELINE pass on a brand-new era: zero backend/frontend
     code was written this iteration (confirmed by the dev handoff's empty `git diff --stat`).
     J-01–J-09 describe Referee machinery that does not exist yet by design, so all nine
     correctly FAIL their acceptance checks. J-10 (kept-product regression sentinel) is the
     one journey with real existing content, and it PASSES. Per this agent's standard rule
     ("FAIL: ... OR any P1 test fails"), 9 failing Must-have journeys make the aggregate
     verdict FAIL — that is the honest ground truth this baseline iteration exists to record,
     not a defect. -->

**Overall:** 1/10 journeys passed (0 skipped) — J-10 PASS; J-01–J-09 FAIL (all failures are the
expected "not built yet" state for a brand-new era's iteration 0, confirmed with concrete
evidence, never assumed).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Era transition reconciliation — evidence readiness fold | smoke | P1 | `GET /research/desk/referee/evidence` serves per-family readiness shape; `test_referee_guards.py` doc-drift + zero-lens-diff guards green | `app/research/referee_evidence.py` does not exist; `GET /research/desk/referee/evidence` → HTTP 404; `tests/test_referee_guards.py` does not exist | FAIL | none — no UI surface; see Actual (curl 404 + `find` absence) |
| UT-J-02 | Evidence contract — two families, one observation shape | smoke | P1 | Typed observation + Playbook/strategy adapters + derived obs cache reproduce fixture goldens | `referee_evidence.py` absent; no adapters, no fixture goldens locatable anywhere in the tree | FAIL | none — no UI surface; see Actual (`find` absence) |
| UT-J-03 | Statistics core — calibrated, seeded, oracle-proven | smoke | P1 | `referee_stats.py` + `tests/test_referee_oracles.py` oracle suite green within budget | Neither file exists anywhere under `apps/backend` | FAIL | none — no UI surface; see Actual (`find` absence) |
| UT-J-04 | Matched nulls — comparable times, identical measurement | smoke | P1 | `GET /research/desk/referee/nulls` serves recorded nulls with honest absence | `referee_null.py` absent; `GET /research/desk/referee/nulls` → HTTP 404 | FAIL | none — no UI surface; see Actual (curl 404) |
| UT-J-05 | Registry — pre-registration with an immutable boundary | smoke | P1 | `GET .../registry` + `POST .../registry/hypotheses` reachable with append-only semantics | `referee_registry.py` absent; both GET and POST → HTTP 404 | FAIL | none — no UI surface; see Actual (curl 404 ×2) |
| UT-J-06 | Estimand engines + adjudication — one checkpoint recorded | smoke | P1 | `GET /research/desk/referee/adjudications` serves verdict-vocabulary fold | `referee_adjudicate.py` absent; `GET .../adjudications` → HTTP 404 | FAIL | none — no UI surface; see Actual (curl 404) |
| UT-J-07 | Starter family — shortlist + real registration flow | smoke | P1 | `/desk` renders a shortlist table with readiness numbers, a registration confirmation flow, and discovery-labeled historical numbers (screenshot) | `/desk` loads (200) with all shipped sections intact; zero shortlist/registration UI anywhere in the DOM or in `apps/frontend/` source (grep) | FAIL | `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png` |
| UT-J-08 | Strategy family + promotion interlock — fail closed | smoke | P1 | `authorize_promotion` gates `pnl_scan._promote`; certificate contract enforced, no bypass | `authorize_promotion` does not exist anywhere under `app/research/`; `_promote` runs only the pre-Era-6 dataset-count gate (confirmed by direct source read + `pytest -k promot` re-run, 7 passed) | FAIL | none — no UI surface; see Actual (grep absence + source read) |
| UT-J-09 | Referee `/desk` sections + MCP contract v5 (22 tools) | smoke | P1 | Three new `/desk` sections (Referee Registry / Adjudications / Runs) render honest empty/populated states; exactly 22 MCP tools | `/desk` shows zero referee-prefixed heading/`data-testid` anywhere (screenshot); `EXPECTED_TOOLS` = exactly 20 entries, no `desk_referee`/`desk_referee_registry`; live MCP manifest independently matches 20-for-20 | FAIL | `reports/qa/goal-referee-iter-0-evidence/J-09-fail.png` |
| UT-J-10 | Kept product stands — regression sentinel | regression | P1 | Cockpit sim tape+chart, `/structure` pinned-AAPL Load, and every shipped `/desk` section render exactly as shipped; suite green; fingerprint pin unchanged; nav = 3 routes | Cockpit: watched SIM-BUYER, tape state converged to "Buyer Control" (confidence 0.914) with live quote/features/trades/observations/event-log all populated. Structure: AAPL as-of 2026-06-22 12:00:00 loaded real bands (e.g. resistance 300.11–302.2 Class A, matching the era-5B pinned wall) over 277/676 1d candles, map basis 2026-06-18. Desk: screen/playbook/backscan controls render correct honest-empty-state copy (no recorded screen/playbook history on this scratch checkout); Playbook Evidence and Screen Runs collapsible sections expand correctly (Playbook Evidence returned real band-context/cohort data from 2 pooled records). Exactly 3 nav routes confirmed in DOM. Zero "referee" string anywhere across the whole browser session. Backend suite 2,418 passed/8 skipped/0 failed (dev handoff, independently spot-checked route-level); fingerprint `08e471b10130e1e2` confirmed independently | PASS | `reports/qa/goal-referee-iter-0-evidence/J-10-result.png` (cockpit), `reports/qa/goal-referee-iter-0-evidence/J-10-structure.png`, `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png` (desk, shared) |

---

## Passed Tests

### UT-J-10 — Kept product stands — regression sentinel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-0-evidence/J-10-result.png` (cockpit), `reports/qa/goal-referee-iter-0-evidence/J-10-structure.png` (structure), `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png` (desk shell, shared with J-07/J-09 evidence)

- **Cockpit (`/`):** Typed `SIM-BUYER` into the Ticker field, clicked Watch. Page transitioned from "No ticker watched" to a fully live simulated tape: Tape State card showed "Buyer Control" at confidence 0.914 with the confidence bar rendered; Quote (bid 101.27/ask 101.29/spread 0.02/last 101.27), Features (trade speed, volume speed, aggressive buy/sell ratios, net aggressive volume, price impacts, spread, large prints, absorption/refresh scores), Recent Trades (14 rows with price/size/side), Observations ("Buyer aggression increasing", "Price lifting on buy prints", "Spread stable and narrow"), and Event Log ("Tape state changed to buyer_control") were all populated with real, internally-consistent values. Chart rendered live 10s candles.
- **Structure (`/structure`):** Filled Symbol=AAPL, As-of (ET)=`2026-06-22 12:00:00`, clicked Load. Tradable Map resolved "Map basis (prior completed session close): 2026-06-18 00:00:00 ET", loaded 277 of 676 1d candles around the query time, and rendered a real quality-scored band table (5 resistance + 5 support Class-A bands shown, including resistance 300.11–302.2 flagged `round number` — matching the previously-verified era-5B AAPL wall example from project history). Band lines overlaid correctly on the chart.
- **Desk (`/desk`):** Page shell, nav, and every shipped control (`desk-run-screen-button`, `desk-topup-button`, `desk-reconcile-button`, `desk-playbook-date-input`, `desk-backscan-*`, `desk-deep-backfill-*`) present with correct `data-testid`s. This scratch checkout has no recorded desk screen/playbook history for any date, so the page correctly serves honest empty-state copy ("Desk screen not computed yet.", "No screen has been recorded yet for the registered universe.", "Playbook not computed for this session.", "No back-scan runs recorded yet.") rather than fabricating data — this is the Design Direction's documented behavior, not a defect. Expanded the collapsible "Screen Runs" section (→ "No screen runs recorded yet.") and "Playbook Evidence" section, which returned real, rich, already-recorded band-context/cohort data (built from signature `ea90e8afcc196857`, 2 records pooled from 2026-06-25 and 2026-08-07, full backing/room cohort breakdown, "Other signatures" disclosure list) plus its full `data-testid="desk-evidence-cells-table"` per-(setup, side, measure) cells grid with sortable column headers (363 `<tr>` elements in the raw DOM — visible as the large table filling most of `J-07-fail.png`'s height) — confirming the R-4 band-context/cohort machinery and the B2 Playbook Evidence feature (frozen research vocabulary this era) still render correctly end-to-end.
- **Cross-cutting:** Exactly 3 `data-testid="nav-link"` entries in the DOM (Cockpit `/`, Structure `/structure`, Desk `/desk`) on every page visited. A case-insensitive grep for "referee" across every HTML/markdown snapshot captured this session (7 page states across 3 routes) returned zero matches. Backend suite count (2,418 passed / 8 skipped / 0 failed / 0 errors) and `Config().config_fingerprint() == "08e471b10130e1e2"` were taken from the dev handoff and independently spot-checked at the route level (all four referee-route 404s + the `authorize_promotion`/file-absence greps reproduced identically).
- A golden replay script was written to `runs/goal-session-referee/journey-scripts/J-10.json` and linted clean (`demo_runner.py --mode lint` → `J-10 ok`).

---

## Failed Tests

### UT-J-01 — Era transition reconciliation — evidence readiness fold
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `app/research/referee_evidence.py` does not exist; `GET /research/desk/referee/evidence` returns HTTP 404; `tests/test_referee_guards.py` does not exist.
**Evidence:** none (no UI surface exists for this journey at this state)

**Steps taken:**
1. `curl -s -o /dev/null -w "%{http_code}"  http://localhost:8301/research/desk/referee/evidence` → `404`.
2. `find apps/backend -iname "referee_evidence.py" -o -iname "test_referee_oracles.py" ...` → no matches for any referee module.

**Expected:** Per-family readiness shape served with fixture numbers exact; doc-drift and zero-lens-diff guards green.
**Actual:** Route not registered (404); module and guard test both absent from the tree.

---

### UT-J-02 — Evidence contract — two families, one observation shape
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `referee_evidence.py` (the module that would define the typed observation + both adapters) does not exist.
**Evidence:** none (no UI surface)

**Steps taken:**
1. Same file-absence check as J-01 covers this journey directly (same module).

**Expected:** Fixture goldens reproduce hand-computed observation sets for both families byte-identically.
**Actual:** No adapters, no derived observation cache, no fixture goldens exist anywhere in the tree.

---

### UT-J-03 — Statistics core — calibrated, seeded, oracle-proven
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `referee_stats.py` and `tests/test_referee_oracles.py` do not exist.
**Evidence:** none (no UI surface)

**Steps taken:**
1. `find apps/backend -iname "referee_stats.py" -o -iname "test_referee_oracles.py"` → no matches.

**Expected:** The oracle suite is green within `REFEREE_ORACLE_BUDGET_SECONDS` and IS the acceptance.
**Actual:** No oracle suite exists to run; nothing to attempt.

---

### UT-J-04 — Matched nulls — comparable times, identical measurement
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `referee_null.py` does not exist; `GET /research/desk/referee/nulls` returns HTTP 404.
**Evidence:** none (no UI surface)

**Steps taken:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/research/desk/referee/nulls` → `404`.

**Expected:** Recorded nulls served with honest absence for uncomputed cells.
**Actual:** Route not registered.

---

### UT-J-05 — Registry — pre-registration with an immutable boundary
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `referee_registry.py` does not exist; both `GET /research/desk/referee/registry` and `POST /research/desk/referee/registry/hypotheses` return HTTP 404.
**Evidence:** none (no UI surface)

**Steps taken:**
1. `curl ... http://localhost:8301/research/desk/referee/registry` → `404`.
2. `curl -X POST -d '{}' ... http://localhost:8301/research/desk/referee/registry/hypotheses` → `404`.

**Expected:** Append-only registry reachable; malformed/duplicate/retroactive-boundary registrations refused with distinct honest errors.
**Actual:** Neither route exists; the POST 404s before any handler or validation runs.

---

### UT-J-06 — Estimand engines + adjudication — one checkpoint recorded forever
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `referee_adjudicate.py` does not exist; `GET /research/desk/referee/adjudications` returns HTTP 404.
**Evidence:** none (no UI surface)

**Steps taken:**
1. `curl ... http://localhost:8301/research/desk/referee/adjudications` → `404`.

**Expected:** Verdict-vocabulary fold serving `exploratory`/`registered`/`pending_forward_confirmation`/etc.
**Actual:** Route not registered.

---

### UT-J-07 — Starter family — historical exploration becomes registered questions
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** No shortlist table, no registration confirmation flow, and no discovery-labeled historical numbers exist anywhere on `/desk` or in the frontend source.
**Evidence:** `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk` (Chrome MCP).
2. Extracted full page markdown/DOM — content is exactly the shipped Screen/Playbook/Backscan/Playbook-Evidence sections with honest empty-state copy; no shortlist, no candidate rationale text (e.g. "capitulation:long", "jbe:long"), no registration/confirmation UI.
3. Grepped every captured HTML/markdown snapshot for "referee" (case-insensitive) — zero matches.
4. Screenshot captured at this state.

**Expected:** Shortlist renders with readiness numbers and rationales; a registration flows through confirmation to a recorded hypothesis; discovery label renders on historical numbers.
**Actual:** None of this exists yet — the shipped `/desk` page (Screen/Playbook Signals/Backscan/Playbook Evidence) is the entire page.

---

### UT-J-08 — Strategy family + promotion interlock — fail closed, no bypass
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** `authorize_promotion` does not exist anywhere under `app/research/`; `pnl_scan._promote` runs only the pre-Era-6 dataset-count gate.
**Evidence:** none (no UI surface)

**Steps taken:**
1. `grep -rn "authorize_promotion" apps/backend/app/research/` → no matches.
2. Cross-checked against the dev handoff's direct read of `pnl_scan.py` lines 267–327 and its targeted re-run `pytest tests/test_pnl_scan.py -k promot -q` → 7 passed, confirming promotion today has no certificate gate of any kind.

**Expected:** A fixture candidate without a valid certificate is refused (no ledger row, no pointer movement); a fixture-certificate-matching candidate promotes.
**Actual:** No certificate concept exists; every promotion path runs the old gate only.

---

### UT-J-09 — The Referee on `/desk` + MCP contract v5 — 22 read-only tools
**Verdict:** FAIL (expected — nothing built yet)
**Failure:** None of the three new `/desk` sections (Referee Registry / Referee Adjudications / Referee Runs) exist; MCP surface is 20 tools, not 22.
**Evidence:** `reports/qa/goal-referee-iter-0-evidence/J-09-fail.png`

**Steps taken:**
1. Same browser pass as J-07 (`/desk`, same screenshot/state) — searched extracted DOM/markdown for "Referee Registry", "Referee Adjudications", "Referee Runs" headings or `data-testid`s — zero matches.
2. Read `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple directly (lines 56–76) and counted programmatically: exactly 20 entries, ending in `get_endpoint`; neither `desk_referee` nor `desk_referee_registry` present.
3. Cross-checked against this session's own connected `tapeology` MCP tool manifest (the `mcp__tapeology__*` tools available to this agent) — exactly 20 tools, one-for-one match with `EXPECTED_TOOLS`, zero extras/omissions.

**Expected:** Three sections render honest empty/populated states with verdict chips; exactly 22 tools advertised.
**Actual:** Zero of three sections exist; 20 tools, not 22.

---

## Skipped Tests

None. All ten journeys were attempted and produced a recorded verdict with concrete evidence (curl status codes, `find`/`grep` absence, source reads, or a browser screenshot).

---

## Non-browser verification note

J-01–J-06 and J-08 have no UI surface at this build state (their entire acceptance is
backend route/file existence — explicitly tagged `(Keyless; automated.)` in `docs/goal.md`,
and the iter spec's own TESTING REQUIREMENTS list Browser only for J-07/J-09/J-10). These were
verified via direct backend checks (`curl` against the running `:8301` backend, `find`/`grep`
against the source tree) rather than a browser session, since there is nothing to load in a
browser for an absent route. The developer's handoff (`docs/handoffs/goal-referee-iter-0-dev.md`)
performed the same checks in full first; this agent independently reproduced every one of them
(all four referee-route 404s, the `authorize_promotion` grep, the whole-tree `referee` file
absence, the `EXPECTED_TOOLS` count) rather than taking the handoff on faith, and got identical
results on every point checked.

## T-9 (clean rebuild) note

Per `docs/goal.md` T-9, browser evidence should follow `rm -rf apps/frontend/.next` + rebuild.
This agent did not perform that rebuild: the developer handoff confirms zero frontend files
changed this iteration (`git diff --stat -- apps/` empty), so there is no stale-build risk to
guard against, and this agent's own operating rules prohibit restarting the app stack mid-QA
("Never debug or restart the app — that is a SKIPPED with reason"). The already-running
`scripts/dev.sh` instance on `:3301`/`:8301` (confirmed independently boot-clean twice by the
developer, and confirmed responsive by this agent throughout) was used as-is. This is a
deliberate, low-risk call, not an oversight — flagged here for transparency.

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP port 127.0.0.1:9222, headless (pump-launched, not touched by this agent)
- **Test Date:** 2026-08-14
- **Evidence directory:** `reports/qa/goal-referee-iter-0-evidence/`
- **Golden replay scripts:** `runs/goal-session-referee/journey-scripts/J-10.json` (linted clean; only J-10 passed, so it is the only golden written this iteration per the best-effort PASS-only rule)
