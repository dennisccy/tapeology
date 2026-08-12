# Phase goal-playbook-iter-11 — UI Test Results

**Phase:** goal-playbook-iter-11
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 1/1 tests passed (0 skipped)

---

## Scope note (lean iteration)

Per this iteration's dispatch, GOAL-MODE LEAN MODE restricted browser-QA to testing **exactly
J-09** this run. J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10 are intentionally **not**
re-driven here — they are verified separately by the deterministic golden-replay lane this same
run (their own `-verify.png` evidence already present in
`reports/qa/goal-playbook-iter-11-evidence/` from that separate pass). This report covers only
J-09.

## Environment confirmation

- Frontend: `http://localhost:3301` — HTTP 200.
- Backend: `http://localhost:8301` — `{"status":"ok"}`.
- **Confirmed the store-scope guard's swap**: `GET /research/desk/universe` on `:8301` reports
  `latest.source_url = "fixture-rig-iter8-replay"`, `latest.member_count = 20` (members
  `DECOR, RTAAA, DTAAA, BSCAN, OHB01..OHB12, CALDR, OLBRK, JBEXP, DBIMP`) — exactly the scoped
  fixture rig named in the dispatch note.
- Chrome MCP attached to the pinned CDP endpoint (127.0.0.1:9222); no new browser was launched,
  no profile/port was changed, headless mode was left as-is.
- No compute/backscan/Run Playbook/Run Screen control was clicked at any point (read-only
  navigation + DOM inspection only) — the operator's real `apps/backend/.data/` store was never
  in the request path (all requests went to the scoped `:8301` rig) and the guard's baseline was
  not touched.
- Re-confirmed both servers healthy and the fixture rig unchanged (`fixture-rig-iter8-replay`,
  20 members) immediately before finishing.

## What "UT-J-09" actually re-verifies this run (TC-1/TC-2 from the iteration spec)

Per the iteration spec's own honest framing: `demo_runner.py` has no MCP/API step type, so a
literal MCP-transport golden is impossible. This run instead does two things, both genuinely
executed this iteration (not carried/deferred):

1. **Live `app.mcp` registry inspection** (mirrors the iteration-9 evaluator's own technique,
   per TC-2) — imported `app.mcp` in the backend's own venv (`apps/backend/.venv/bin/python`)
   and `await`-called the actual registered `list_tools()` handler (the same coroutine the
   `mcp.server.lowlevel.Server` dispatches at runtime — not a static grep):
   ```
   live tool count: 20
   TOOL_NAMES module constant count: 20
   live names == TOOL_NAMES: True
   desk_playbook present: True
   desk_playbook_evidence present: True
   ```
   Full live order: `tape_state, tape_features, tape_history, datasets, bars, levels,
   tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen,
   desk_forward, desk_playbook, desk_playbook_evidence, pnl_ledger, taxonomy, ui_route_map,
   get_endpoint` — matches `EXPECTED_TOOLS`/`TOOL_NAMES` exactly, both new tools present by
   name at positions 15/16.
2. **New `/desk` golden replay script** (`runs/goal-session-playbook/journey-scripts/J-09.json`,
   did not exist before this run) — navigates to `/desk` and asserts the static, already-shipped
   label text `"Built from signature:"` inside the Playbook Evidence section
   (`data-testid="desk-evidence-signature"`, `page.tsx:3926-3927`), deliberately never the
   dynamic hash beside it. Verified two ways this run: (a) live browser navigation + DOM
   `extract` returned `Built from signature: 9ba29d8e3aaaa643` verbatim; (b) `demo_runner.py
   --mode lint --scripts-dir runs/goal-session-playbook/journey-scripts --journeys J-09` →
   `J-09 ok`. Checked for collisions against all 9 other stored goldens (J-01–J-08, J-10) for
   both the label text and the testid — none found (T-11).

**Honesty note on what this does and does not prove** (per the dispatch's explicit caution not
to overstate): the golden proves the `/desk` page renders the `desk_playbook_evidence`-backed
section's static shell text — i.e., that data-contract row is being served and rendered, and
gives fast future regression coverage for that fact. It does **not** exercise the MCP stdio
transport, tool-call dispatch, or the byte-identity-vs-curl / allowlist-refusal behavior — that
half of J-09's acceptance is, and remains, covered by the already-existing, already-pinned
`apps/backend/tests/test_mcp_server.py` (`EXPECTED_TOOLS`/`TOOL_NAMES` at :56/:198, the
byte-identity tests for both new tools in empty AND populated fixture states, and the
`get_endpoint` `?date=` proxy test) — not re-run in full by this browser-QA pass (out of this
agent's lane; it is the backend suite's job, tracked separately under TC-12).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-09 | MCP contract v4 — 20 read-only tools | integration (live registry, keyless) + browser (golden shell-string regression) | P1 | Live `app.mcp` tool registry advertises exactly 20 tools; `desk_playbook` and `desk_playbook_evidence` present by name; `/desk` renders the Playbook Evidence section's static "Built from signature:" label (the data-contract row the new tools proxy); a lint-clean golden replay script exists for future re-verification | Live import of `app.mcp.list_tools()` returned exactly 20 tools matching `EXPECTED_TOOLS`/`TOOL_NAMES` byte-for-byte, both `desk_playbook`/`desk_playbook_evidence` present at positions 15/16. Navigated to `http://localhost:3301/desk` on the confirmed scoped fixture rig (`fixture-rig-iter8-replay`, 20 members); Playbook Evidence section rendered `"Built from signature: 9ba29d8e3aaaa643"` (DOM `extract` verbatim match on the label). Screenshot captured. New golden `runs/goal-session-playbook/journey-scripts/J-09.json` authored and passes `demo_runner.py --mode lint`. No console errors (only the standard React DevTools info line). | PASS | `reports/qa/goal-playbook-iter-11-evidence/UT-J-09-result.png` |

---

## Passed Tests

### UT-J-09 — MCP contract v4 — 20 read-only tools
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-11-evidence/UT-J-09-result.png`
- Confirmed the scoped fixture rig is live on `:8301`/`:3301` (`source_url="fixture-rig-iter8-replay"`, 20 members) before testing.
- Live-invoked `app.mcp.list_tools()` in the backend's own venv (not a static grep) — 20 tools returned, order and names byte-identical to the pinned `EXPECTED_TOOLS`/`TOOL_NAMES` constants; `desk_playbook` and `desk_playbook_evidence` both present by name.
- Navigated Chrome MCP to `/desk`; waited for `[data-testid="desk-evidence-signature"]`; `extract`-ed its text and got `Built from signature: 9ba29d8e3aaaa643` — confirms the static label the new golden asserts on, distinct from J-01's ("Playbook Signals") and J-08's (the evidence-cell CSS selector) own assertions, and confirmed via grep against all 9 other stored goldens that no collision exists.
- Took the acceptance screenshot (had to enlarge the viewport to 1280×3000 and keep `scrollY=0` to get a non-blank capture — see Notes below — rather than scrolling a shorter viewport, which reproducibly rendered blank in this headless session).
- Authored `runs/goal-session-playbook/journey-scripts/J-09.json` (single `goto /desk` + `expect text "Built from signature:"` step, mirroring J-01's own goto+expect shape); `demo_runner.py --mode lint` returned `J-09 ok`.
- Did not click any compute/Run Playbook/Run Screen/Backscan control; re-confirmed both servers healthy and the fixture rig's `source_url`/`member_count` unchanged immediately after.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10 were intentionally not driven by this
agent this run per the lean-mode dispatch (deterministic replay covers them separately this same
run) — not a SKIP of this agent's own assigned scope, which was J-09 only.

---

## Notes

- **Headless screenshot-after-scroll quirk observed and worked around.** On this specific `/desk`
  page, taking a screenshot after scrolling the viewport down (`element.scrollIntoView`, native
  `hover`, or plain `window.scrollTo` were all tried) reproducibly returned a fully blank
  (solid-background) PNG in this headless Chrome session, even though `getBoundingClientRect()`
  and DOM `extract` both confirmed the target element was correctly positioned inside the
  viewport. This was **not** a functional/rendering failure of the app — the DOM content was
  provably present and correct throughout (confirmed via `extract` before, during, and after).
  Root cause not chased further (out of this agent's remit — no source was edited). Workaround
  that produced a valid, content-showing screenshot: enlarge the viewport itself
  (`set_viewport` to 1280×3000) so the target element falls inside the viewport at `scrollY=0`,
  instead of scrolling a shorter viewport down to it. Recorded here in case this recurs on other
  long `/desk` pages in future iterations.
- This iteration's own golden did not need any interactive setup (no compute click, no date
  input) because the Playbook Evidence section loads via a page-load GET, not a triggered
  compute (T-7) — consistent with J-08's existing golden, which also asserts on this section
  without clicking anything first.
- `runs/goal-session-playbook/state/golden-gaps` was already absent before this run and both of
  this iteration's TC-1/TC-2 conditions landed in the same run, so per the iteration spec's own
  described self-healing mechanism it should stay absent — this agent did not touch that file
  directly (bookkeeping owned by `replay-lane.sh`'s `replay_lane_golden_coverage`, outside this
  agent's assigned scope this run).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped fixture rig, `source_url="fixture-rig-iter8-replay"`, 20 members)
- **Browser:** Chrome via MCP (headless, pinned CDP 127.0.0.1:9222; not modified)
- **Test Date:** 2026-08-12
- **Evidence directory:** `reports/qa/goal-playbook-iter-11-evidence/`
