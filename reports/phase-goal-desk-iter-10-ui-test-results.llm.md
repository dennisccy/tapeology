# Phase goal-desk-iter-10 — UI Test Results

**Phase:** goal-desk-iter-10
**Date:** 2026-07-28
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 2/2 tests passed (0 skipped)

**Lean-mode scope note:** per this run's dispatch, browser-qa-agent tested EXACTLY J-06 and J-08
this iteration. J-01, J-02, J-03, J-04, J-05, J-07 were deliberately **not** re-tested here — they
are covered by the deterministic golden replay, already run separately this iteration and reported
**6/6 PASS** in `reports/phase-goal-desk-iter-10-smoke-replay-results.md` (same scoped backend, see
that report's own "Scoped data root" section). This report does not duplicate that work.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | smoke | P1 | `/desk` (default/latest view) legibly shows one ranked row with `basis_age_days <= 2` and one with `basis_age_days >= 10`, both in a single screenshot | Live browser load of `/desk` on the scoped rig rendered the new `screen-2026-07-25` snapshot (63 rows/38 skipped); rows 0-3/5-11 (BRK-B, DHR, HD, IBM, CRM, AMT, HONA, LOW, LIN, CAT, COST...) read `basis 2026-07-23 · 2 d before as-of` and row 4 (NFLX) reads `basis 2026-07-13 · 12 d before as-of` — both legible together, no scrolling needed | PASS | `reports/qa/goal-desk-iter-10-evidence/UT-J-08-result.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | contract | P1 | MCP server advertises exactly 17 read-only tools incl. `desk_universe`/`desk_screen`; byte-identical GET-proxy behavior; honest-error on an unreachable backend (no fabrication) | This session's live tool roster = exactly 17 `mcp__tapeology__*` tools matching `test_mcp_server.py`'s `EXPECTED_TOOLS` tuple verbatim (name-for-name); a fresh, independent re-run of `tests/test_mcp_server.py` (not reused from any other lane) = **34/34 passed**; a live call to `mcp__tapeology__ui_route_map` against the (deliberately not-started this iteration) ambient backend returned an honest `ConnectError... no cached or fabricated data is served` — correct read-only, no-fallback behavior, not a defect | PASS | N/A — no browser surface (see Note below); evidence = pytest transcript + live tool-call transcript, both reproduced in this report |

---

## Passed Tests

### UT-J-08 — Every ranked briefing row names the bar its distance was measured from
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-10-evidence/UT-J-08-result.png`

Steps executed (goal.md's J-08 "Steps" are backend build steps, already shipped in iteration 9 and
byte-unmodified this iteration; the only browser-testable surface is the Acceptance clause, which is
what this test executes):

1. Navigated Chrome MCP to `http://localhost:3301/desk` (the scoped rig's frontend, pointed at the
   scoped backend on `:8301`) — nav renders **Cockpit · Structure · Desk**, heading "Desk" present,
   no console errors of note.
2. Set viewport to 1600×1100 (desktop-representative size) so the full ranked table (symbol, side,
   class, distance, score, coverage, tick evidence, basis) renders without horizontal scroll.
3. Confirmed via DOM query (`[data-testid="desk-screen-rows-table"]` present; 63
   `[data-testid="desk-row-basis"]` cells) that the DEFAULT/latest view is the NEW
   `screen-2026-07-25` snapshot the dev lane computed this iteration (63 rows / 38 skipped,
   `config_fingerprint 08e471b10130e1e2`, `as_of 2026-07-25T23:59:59Z`) — **not** stale/loading:
   `desk-title` innerText = `"Desk"`, `desk-screen-loading` absent, no "Desk screen not computed
   yet." text anywhere on the page.
4. Read each basis cell's literal text via DOM query (not just visual inspection): row 0 (BRK-B) =
   `"basis 2026-07-23 · 2 d before as-of"` (age 2, satisfies `<= 2 d`); row 4 (NFLX) =
   `"basis 2026-07-13 · 12 d before as-of"` (age 12, satisfies `>= 10 d`). Both rows are within the
   first 5 ranked rows, so no scroll was needed for either.
5. Captured one viewport screenshot at scroll position 0
   (`reports/qa/goal-desk-iter-10-evidence/UT-J-08-result.png`) — legibly shows the Provenance box
   (universe snapshot, screen date 2026-07-25, as-of, fingerprint, bar-store signature) and the
   ranked table's `basis` column with **BRK-B/DHR/HD/IBM (2 d before as-of)** and **NFLX
   (12 d before as-of)** together in the same image, satisfying the literal `<= 2 d` / `>= 10 d`
   thresholds (TC-11: no softened variant used — these are the literal numbers).
6. Zero mutating interaction performed: no click on Run Screen, Top-up, or any history row — pure
   navigation + read-only DOM queries + screenshot, per the iter spec's Lessons-applied (iii)
   constraint and the dev handoff's "reading only" warning for this scoped instance.

**Golden replay script:** `runs/goal-session-desk/journey-scripts/J-08.json` was **left unmodified**
by this agent. It already contains a dev-lane-added `notes` field disclosing that its steps 4-6
(history-row navigation) are environmentally fragile against any store holding two `screen_date
2026-07-25` recordings — exactly this scoped root's current state — which is why the SEPARATE
deterministic replay of that script legitimately reported FAIL at step 4 this iteration (see
`reports/phase-goal-desk-iter-10-j08-replay-results.md`). That is a different, already-disclosed
artifact from this agent's own live verification above. This agent did not rewrite the script to
route around the same-date ambiguity because reopening that ambiguity is explicitly OUT OF SCOPE
for this iteration ("Re-opening ... the same-date screen ambiguity ... — carried, unrelated to this
journey"); the live-browser check above independently confirms the literal DoD screenshot
requirement without depending on the fragile history-row flow, consistent with the dev handoff's
own conclusion that "[the step-4 replay failure] does not affect the actual DoD criterion, which
needs no history-row click."

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** PASS
**Evidence:** N/A screenshot (J-06 has **no browser surface** — goal.md tags it
`*(Keyless; automated.)*` explicitly); transcript evidence below.

J-06's goal.md "Steps" are all code/test changes (already shipped, byte-unmodified this iteration
per the iter spec's IN SCOPE list). Its Acceptance is a protocol-level contract with nothing to
click or screenshot. Since browser automation does not apply, this agent verified it through the
closest available real evidence — direct MCP tool invocation plus an independent fresh test run —
rather than marking it SKIPPED (which would be inaccurate; genuine verification was possible and was
performed):

1. **Tool-roster count (this live session):** exactly 17 `mcp__tapeology__*` tools are loadable —
   `backtests, bars, datasets, desk_screen, desk_universe, edge_report, get_endpoint, levels,
   pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability,
   ui_route_map`. Cross-checked name-for-name (order-independent) against `EXPECTED_TOOLS` in
   `apps/backend/tests/test_mcp_server.py:52-70` — identical 17-entry set, including the two new
   tools this era added (`desk_universe`, `desk_screen`).
2. **Fresh, independent test run (this agent's own, not reused from the dev handoff's earlier run):**
   ```
   cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -v
   ```
   Result: **34 passed** (0 failed), covering the `EXPECTED_TOOLS` tuple assertion, the
   read-only/no-write-verb-in-tool-name assertion, and the byte-identity/honest-error clauses this
   file pins.
3. **Live tool-call attempt:** invoked `mcp__tapeology__ui_route_map` (a zero-argument GET proxy of
   `/meta/ui-routes`). This session's MCP server is configured (`.mcp.json`) with
   `TAPEOLOGY_API_BASE=http://localhost:8000` — the **ambient** backend, which this iteration
   deliberately never starts (only the scoped `:8301` pair is up, per the iter spec's scoped-only
   discipline). The call returned:
   ```
   tapeology backend unreachable at http://localhost:8000 (GET /meta/ui-routes): ConnectError:
   All connection attempts failed — no cached or fabricated data is served
   ```
   This is the **expected, correct** result given the environment (ambient backend intentionally not
   running this iteration) — not a defect. It is also independently useful evidence: it demonstrates
   the MCP proxy's honest-failure behavior firsthand (refuses to fabricate or serve stale data when
   its backend is unreachable), consistent with the project's read-only/no-fabrication rails.

Combined, this is genuine, independently-gathered (not merely re-stated from another lane's claim)
evidence that J-06's 17-tool contract holds. No product code was touched to produce it (pure reads:
tool listing, pytest execution, one GET-proxy call).

**Golden replay script:** none written for J-06 (`runs/goal-session-desk/journey-scripts/` has no
`J-06.json` and this agent did not create one) — the golden-script mechanism replays a **browser**
flow via `demo_runner.py`, and J-06 has no browser flow to encode. This is consistent with every
prior iteration's handling of J-06 (no `J-06.json` has ever existed in that directory).

---

## Failed Tests

None.

---

## Skipped Tests

None. Both journeys assigned to this lean-mode dispatch (J-06, J-08) were fully exercised with real
evidence; neither was skipped.

---

## Scoped data root (TC-3 disclosure — absolute path used for every capture this run)

Every action in this report (both the J-08 browser navigation and, indirectly, the environment state
J-06's live tool-call attempt observed) ran against the **scoped rig**, never the ambient
`apps/backend/.data/` store:

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa
```

Backend served on `http://localhost:8301` (uvicorn), frontend on `http://localhost:3301`
(next-server), both already running at dispatch start (seeded/started by the developer lane; this
agent did not reseed, restart, or write to this root — read-only navigation, DOM queries, and
screenshots only). The ambient backend (`:8000`) and ambient frontend (`:3000`) were confirmed
**not running** at the time of this QA pass (`curl` → connection refused on both); this agent did
not start them. No file under the ambient `apps/backend/.data/` tree was read, computed against, or
written by this agent.

---

## Environment

- **Frontend URL:** http://localhost:3301 (scoped rig; ambient `:3000` not running)
- **Backend URL:** http://localhost:8301 (scoped rig; ambient `:8000` not running, confirmed via curl)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to
  existing headless Chrome on CDP port 9222 (auto-restarted transparently on first navigate; browser
  tool re-attached and completed the navigation successfully)
- **Test Date:** 2026-07-28
- **Evidence directory:** `reports/qa/goal-desk-iter-10-evidence/`
- **Journeys tested this dispatch:** J-06, J-08 (per lean-mode scope). J-01, J-02, J-03, J-04, J-05,
  J-07 intentionally not tested here — see `reports/phase-goal-desk-iter-10-smoke-replay-results.md`
  (6/6 PASS, same scoped backend).
