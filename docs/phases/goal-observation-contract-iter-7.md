# Goal Iteration 7 — Close J-05's Deferred Row: Evidence-Only Re-Verification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 7
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06
- **Required-still-passing journeys:** none — all six session journeys are already Target journeys this round; the journey set is finite and fixed ("The journey set J-01…J-06 is finite and fixed", docs/goal.md)
- **Anti-goal reminders:**
  - "**No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.)"
  - "**Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - "**Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state."
  - "No new UI page, panel, link, component or frontend file change; no new `Config` field; no named MCP tool; no CLI; no WebSocket embedding; no listing endpoint."
  - "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."
  - "No Goal Mode workaround that edits, deletes, skips or xfails a guard merely to pass a journey."
  - "No browser proof based on a fabricated state presented as real; fixture and real views must be visibly distinguished."
  - "No weakening or bypass of `project-extensions/host-guard/host-guard.env`; Goal Mode pauses `AWAITING_HOST_GUARD` if confinement cannot be established."
  - "No post-`GOAL_ACHIEVED` proposer or `AUTO:journeys` self-extension (the proposer is retired upstream)."
  - "Anti-goal violations use the existing Goal Mode violation state/disposition machinery; they are never dismissed in prose."

## GOAL

Capture fresh, own-row browser-qa evidence for J-05 (the machine-only observation path and its 404 sibling) and, time permitting in the same single dispatch, re-verify J-01..J-04 and J-06, so the results table carries zero deferred or skipped rows and the deterministic `goal_gate.py results` gate passes alongside the already-green `goal_gate.py journeys` gate (6/6).

## BACKGROUND

Iteration 6 (CONTINUE, full depth) finished all product work: J-04 and J-06 moved partial→passing, and J-01/J-02/J-03 were re-verified passing through their own rows. Its results file (`reports/phase-goal-observation-contract-iter-6-ui-test-results.md`) shows 13/14 rows PASS, but `UT-J-05` — "J-05 regression re-check" — was shed as `DEFERRED-BUDGET` because the round ran out of wall-clock time. J-05's substance was fully exercised that round under other row ids (UT-04's served JSON, UT-07's 404 body, the green `test_tape_observation_route.py` run), so journey-history correctly keeps J-05 `passing`, but `goal_gate.py results` blocks `GOAL_ACHIEVED` on the missing ROW, not on the substance — a pure bookkeeping gap, not a product gap. The iter-6 evaluator's next-step recommendation is explicit and unambiguous: re-open `/tape/SIM-BIDABS/observation` (watched, live) and `/tape/ZZZZ/observation` (not watched) in the browser, screenshot both under J-05's own id, re-run the other five rows if time allows, and "use `evidence` depth so no developer or reviewer runs and the round stays short." All six Target journeys are already recorded `passing` (journey-history digest) and this iteration's only deliverable is evidence capture — this is exactly the rule-7 exception to "never plan an evidence-only iteration," so `Depth: evidence` is written directly rather than treated as a trigger to justify. No escape condition for `full` applies either: iteration 6's verdict was CONTINUE (not ESCALATE/REGRESSION), its coherence verdict was COHERENCE-PASS, the hardening-cadence counter is 0/6 (reset by iteration 6's full depth), and no brand-new journey exists — so the evaluator's `evidence` recommendation stands as binding with no override needed. Per the priority rubric, there is no FAILING or PARTIAL journey to pick (6/6 passing) — Target journeys lists the full fixed set instead of a subset, per rule 7.

Two lessons apply directly. First (iter-5): the deterministic replay lane cannot reach a backend-only URL — `demo_runner.py`'s `normalize_url()` rewrites even an absolute `:8301` URL onto the frontend origin, so every `/tape/*` golden assertion renders Next.js's own 404 page and false-FAILs; J-05's evidence must come from the LLM browser-qa lane, which navigates the backend origin directly, never from a regenerated golden script. Second (iter-5): two browser-qa dispatches in one iteration silently destroy each other's evidence (a second dispatch's `llm.md` overwrote the first's, downgrading real PASS rows to SKIP in the merge) — this iteration must run as exactly ONE browser-qa dispatch covering J-05's fresh capture plus any time-permitting re-verification of the other five rows, never a canary-plus-follow-up split. Third (iter-6): in a closing/verification round, run the cheap already-passing row FIRST — J-05's own row (two page loads) must be captured before spending any remaining budget re-verifying the other five, so a repeat budget trim still leaves the one blocking row closed.

## IN SCOPE

### Backend
- None — zero backend code changes. `Depth: evidence` skips the developer and reviewer steps entirely; the entire Binding Execution Order (steps 1-6) is already built and verified per "Do not redo."

### Frontend
- None — zero frontend code changes (era constraint: `Frontend Present: no`; no page, panel, link or component exists to touch).

### Evidence capture (browser-qa-agent only — the actual deliverable of this iteration)
- [ ] FIRST: watch SIM-BIDABS via Cockpit `/` (Simulated → ticker `SIM-BIDABS` → Watch) until the status control reads "live".
- [ ] Open `/tape/SIM-BIDABS/observation` directly in the browser; screenshot the served JSON (HTTP 200) as J-05's own fresh evidence — not reused from UT-04 or any other row's capture.
- [ ] Open `/tape/ZZZZ/observation` directly in the browser; screenshot the 404 "not being watched" body as J-05's second fresh evidence.
- [ ] Record both captures under J-05's own row (e.g. `UT-J-05`) in this iteration's `ui-test-results.md` with a real Verdict and evidence path — it must not read `DEFERRED-BUDGET`, `SKIP`, or `unknown`.
- [ ] Time permitting, in the SAME dispatch: repeat Watch → Pause → Resume → Stop → re-Watch for J-03, re-open the observation address for J-01/J-02/J-04's own rows, and reload `/`, `/structure`, `/desk` plus the nav check for J-06, so every row carries evidence freshly dated this iteration. If budget runs out after J-05, stopping here is a fully valid closing round — the other five rows keep iteration-6's recorded PASS status unchanged.
- [ ] Run this as exactly ONE browser-qa dispatch — no canary dispatch followed by a separate follow-up dispatch (iter-5 lesson: a second dispatch's merge can silently downgrade the first dispatch's real PASS rows to SKIP).

### New user-facing capability
None — no product behavior changes this iteration.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — `/`, `/structure`, `/desk` render exactly as before (re-verified, not modified).

### Product surface delta
None. The only artifact this iteration produces is a fresh `ui-test-results.md` (plus its evidence screenshots) closing a bookkeeping gap; no served value, endpoint, or page changes.

### Blueprint conformance
No new surfaces. `state/blueprint.md` was reviewed this iteration and needs no edit: all evidence is captured against homes it already registers — Cockpit `/` (control-only, to start/pause/resume/stop the Sim watch) and the machine-only path `GET /tape/{ticker}/observation` (the canonical home for J-01..J-05 since iter-5; J-06 is the cross-cutting `/`, `/structure`, `/desk` regression check). No nav-skeleton change; no `blueprint.reapproval-requested` file needed.

### Data-contract additions
None — zero code changes this iteration; all four Data Contract rows in `blueprint.md` (machine-observation semantics, provenance/source/lifecycle metadata, explanatory metadata, integrity) stay exactly as registered since iter-5/iter-6.

## OUT OF SCOPE

- Any change to `apps/backend/` or `apps/frontend/` — this is a capture-only round; Depth: evidence means no developer or reviewer step runs at all.
- Any new guard, test, or spec text — the guard suite (`test_tape_observation_guards.py`, 23 tests) and the full 45-item Required Trap Coverage are already complete per "Do not redo."
- Re-opening the five non-blocking audit GAP notes (mutator-scan receiver name, external-system scan file-type coverage, counter-example blanking, per-module provider isolation, English-only counter-test container) — explicitly flagged "Do NOT open new work for these" in iteration-state.
- Fixing the deterministic replay lane's `normalize_url()` backend-URL rewrite fault — tracked as a framework/tooling issue, not a product issue; `goldens-regen-pending` / `golden-gaps` stay QUEUED, not actioned here.
- Widening the regression set beyond J-01..J-06 — this session's journey set is finite and fixed; there is no seventh journey to add.
- Re-pinning or changing the fingerprint (`08e471b10130e1e2`), the MCP contract (v8/28 tools), or the backend suite count — nothing this round touches code that could move them.

## DEFINITION OF DONE

- [ ] J-05's own row shows PASS in this iteration's `ui-test-results.md`, backed by two fresh screenshots: `/tape/SIM-BIDABS/observation` while watched+live (HTTP 200, full JSON) and `/tape/ZZZZ/observation` (HTTP 404, not-watched body).
- [ ] `goal_gate.py results` exits 0 for this iteration's results file (alongside `goal_gate.py journeys`, already 6/6 passing).
- [ ] Best-effort: J-01, J-02, J-03, J-04 and J-06's own rows are also re-verified this round if time remains, so the merged file carries zero DEFERRED/SKIP rows session-wide; if the round runs out of time after J-05, their prior recorded passing status stands unchanged and this is still a complete iteration.
- [ ] Exactly one browser-qa dispatch runs this iteration — no split canary/follow-up dispatch, and no `.canary.md` sibling shows a PASS row the merge downgraded to SKIP.
- [ ] No anti-goal violation introduced (scan-report stays CLEAN; coherence stays COHERENCE-PASS).
- [ ] Zero code changes: `git diff --stat -- apps/backend apps/frontend` is empty at the end of this iteration.
- [ ] No regression: the six-journey set stays at 6 passing / 0 failing / 0 partial / 0 unknown after this round.
- [ ] `state/blueprint.md` needs no edit this iteration (confirmed: no new displayed value or page) — verified, not modified.
- [ ] Dev handoff: N/A — `Depth: evidence` skips the developer and reviewer steps; no code changes this iteration.

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04, J-05, J-06 — own-row re-verification via the LLM browser-qa lane (never the deterministic replay lane for `/tape/*` paths, per the iter-5 lesson). J-05 is the mandatory row; the other five are best-effort in the same dispatch.
- Unit/integration: none — zero code changes this iteration; the standing backend suite (4075 collected / 8 skipped / 0 failed) and `tsc` (0 errors) are not exercised by this spec's own execution because no developer or reviewer step runs at `Depth: evidence`.
- Error cases: the unwatched-ticker 404 path (`/tape/ZZZZ/observation`) must be captured again as part of J-05's own evidence, matching the byte-identical sibling `/tape/ZZZZ/state` 404 already proven in iteration 6 (UT-07).

Test-first contract:

- TC-1: given a fresh Cockpit `/` page load with no ticker watched, when the operator selects Simulated, enters ticker `SIM-BIDABS` and clicks Watch, then the status control shows "live" on the page.
- TC-2: given SIM-BIDABS is watched and live, when the browser navigates to `/tape/SIM-BIDABS/observation`, then the response is HTTP 200 with a JSON body whose first three keys read `"schema_version":"tape-observation-v1"`, `"provider":"tapeology"`, `"ticker":"SIM-BIDABS"`, captured as J-05's own fresh screenshot.
- TC-3: given no watch exists for ticker `ZZZZ`, when the browser navigates to `/tape/ZZZZ/observation`, then the response is HTTP 404 with body exactly `{"detail":"Ticker 'ZZZZ' is not being watched"}`, captured as J-05's second fresh screenshot.
- TC-4: given both J-05 screenshots exist, when this iteration's merged `ui-test-results.md` is written, then J-05's own row reads PASS with both evidence file paths listed, and a subsequent run of `goal_gate.py results` exits 0.
- TC-5: given exactly one browser-qa dispatch is invoked this iteration, when the merge step runs, then no `.canary.md` sibling exists whose PASS rows were downgraded to SKIP in the merged `ui-test-results.md` (the iter-5 dual-dispatch failure mode).
- TC-6: given wall-clock budget remains after J-05's two captures, when the browser-qa-agent re-opens the Watch → Pause → Resume → Stop → re-Watch cycle and the observation/404 pair again for J-01..J-04 and J-06, then each of those rows reads PASS with a fresh evidence path dated this iteration; if budget runs out first, their rows keep iteration-6's PASS status unchanged and this is not a failure of this iteration.
- TC-7: given this iteration runs at `Depth: evidence`, when the iteration completes, then `git diff --stat -- apps/backend apps/frontend` prints no output (zero code changed).
- TC-8: given this iteration introduces no code change, when the anti-goal scan and coherence audit run against the unchanged tree, then the scan-report stays CLEAN and coherence stays COHERENCE-PASS with no new violation.

## NOTES

- This spec exists to close a bookkeeping gap, not a product gap: journey-history already reads 6/6 `passing`; the deterministic gate is blocked only because `UT-J-05`'s row in iteration 6's results file was shed as `DEFERRED-BUDGET` rather than filled with a real PASS. `goal_gate.py results` checks the row, not the substance (iter-6 lesson).
- If, after this iteration, all six rows are fresh and `goal_gate.py results` exits 0 with no open anti-goal disposition, the evaluator has the standing basis to consider `GOAL_ACHIEVED` — this spec does not declare it (only the evaluator does), and per "Do not redo," no further product code is needed to finish this era.
- Escalation flag: none. This is a low-risk, zero-diff verification round; if the browser-qa dispatch cannot reach the backend origin at all (host-guard, port, or environment failure), report it as a blocker rather than substituting a fixture-based or fabricated capture (anti-goal: "No browser proof based on a fabricated state presented as real").
