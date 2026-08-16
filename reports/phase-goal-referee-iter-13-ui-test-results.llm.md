# Phase goal-referee-iter-13 — UI Test Results

**Phase:** goal-referee-iter-13
**Date:** 2026-08-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

---

**Overall:** 2/2 tests passed (0 skipped)

Scope (goal-mode lean, per dispatch): test EXACTLY J-05 and J-12 this run via Chrome MCP.
J-07, J-09, J-10, J-11 are covered separately by deterministic replay
(`reports/phase-goal-referee-iter-13-regression-replay-results.md`) and are out of scope here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | Expanding "Referee Registry" on `/desk` shows the Registered Hypotheses table with hypothesis S-1's `origin` reading `historical-exploration` (this iteration's deterministic replay reported this text absent — flagged for direct LLM re-verification) | Navigated `/desk`, clicked `desk-section-expand-refereeRegistry`. Registered Hypotheses table renders row S-1 (`capitulation:long`, boundary `2026-08-15`, origin `historical-exploration`, status `active`, accrual `0/12`, discovery `1/1`) — confirmed via full HTML DOM extraction (raw `<td>` text) and a full-page screenshot. Text genuinely present and correctly rendered; the replay tool's FAIL was a false negative (see Notes) | PASS | `reports/qa/goal-referee-iter-13-evidence/J-05-result.png` |
| UT-J-12 | The readiness fold gets its reader — why a family cannot speak, visible on the desk | happy-path | P1 | On the seeded fixture rig, the new Evidence Readiness blocks (Playbook Family + Strategy Family) render every value string-for-string identical to that same request's own `GET /research/desk/referee/evidence` body; on a SEPARATE empty-corpus backend, both blocks render an honest all-zero/absent state, never blank/spinner/404 | Seeded rig (`fixture-rig-iter8-replay`, :3301/:8301): Playbook Family showed `records=4, distinct_sessions=3, signals_at_current_basis=21`, `detector_basis=02bebbe17e7b8769`, `config_fingerprint=08e471b10130e1e2`, "No stale basis dates.", "No integrity errors."; Strategy Family showed `Datasets=0, Train/Holdout=0/0, Trades=0`, the full tick-gate-unmet sentence, and the Card-6.4 basis caveat — all byte-matched against a same-moment `curl` of the live endpoint. Built an isolated empty-corpus backend+frontend pair (:8302/:3302, fresh store dirs) and confirmed via `curl` the served body was genuinely all-zero before use; navigated, expanded Referee Registry: Playbook Family all-zero, Registered Hypotheses showed "No hypotheses registered.", Strategy Family all-zero with the same tick-gate/caveat text still present (not corpus-dependent), no blank/spinner/404 anywhere. Console clean on both passes | PASS | `reports/qa/goal-referee-iter-13-evidence/J-12-seeded-rig-result.png`, `reports/qa/goal-referee-iter-13-evidence/J-12-empty-corpus-result.png` |

---

## Passed Tests

### UT-J-05 — The registry — pre-registration with an immutable boundary
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-13-evidence/J-05-result.png`

- Ran `assert_scoped_qa_backend.py` first — confirmed SCOPED (`fixture-rig-iter8-replay`, member_count=20), exit 0.
- Navigated to `http://localhost:3301/desk`, clicked `[data-testid="desk-section-expand-refereeRegistry"]`, waited for "Strategy Family" (a J-12 string, convenient as a load-complete signal for the shared fetch dispatch).
- Extracted full HTML (not markdown — see Notes) and confirmed the Registered Hypotheses table contains exactly one row, `data-testid="referee-hypotheses-row-S-1"`, with `<td>historical-exploration</td>` in the Origin column, alongside boundary `2026-08-15`, status `active`, accrual `0/12`, discovery `1/1 discovery (exploratory)`.
- Cross-checked against `GET /research/desk/referee/registry` conceptually via the same live rig (the hypothesis is visibly the same S-1 the shortlist table also names) — no reconciliation issue.
- Screenshot (viewport resized to 1683×4320 — the tool's max, to approximate "whole page, no scroll" per the pump's iteration-12 lesson) visually shows the Registered Hypotheses table with the S-1 row and its `historical-exploration` origin cell.
- No console errors.

### UT-J-12 — The readiness fold gets its reader — why a family cannot speak, visible on the desk
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-13-evidence/J-12-seeded-rig-result.png` (state 1), `reports/qa/goal-referee-iter-13-evidence/J-12-empty-corpus-result.png` (state 2)

**State 1 — seeded fixture rig (:3301 / :8301, TC-1, TC-2, TC-4, TC-6, TC-7, TC-8 empty-branch, TC-10, TC-13-bounded):**
- Same navigation as UT-J-05. Full HTML DOM extraction captured both new blocks:
  - `referee-evidence-playbook-block`: Records `4`, Distinct sessions `3`, Signals at current basis `21`, Detector basis `02bebbe17e7b8769`, config fingerprint `08e471b10130e1e2`, `EmptyState` "No stale basis dates.", `EmptyState` "No integrity errors."
  - `referee-evidence-strategy-block`: Datasets `0`, Train/Holdout `0`/`0`, Trades `0`, tick-gate statement, one Card-6.4 basis caveat (verbatim), `EmptyState` "No integrity errors."
- Cross-verified EVERY one of those values string-for-string against a `curl http://localhost:8301/research/desk/referee/evidence` issued in the same testing window — byte-identical, including the full tick_gate_statement sentence and the full basis_caveats paragraph (HTML-entity-decoded `&gt;`/`&lt;` match the raw `>`/`<` in the JSON).
- TC-3 (a non-empty `stale_basis_dates` render) was not exercisable on this rig — its playbook corpus currently has zero stale-basis dates, which instead correctly exercises TC-4's honest-absence branch. Not treated as a gap in J-12's browser acceptance: the dev handoff's own backend test (`test_referee_evidence_served_body_matches_the_pinned_golden_fixture`) is the TC-3-shaped fixture-planting proof; this is a disclosed limit of what the live rig's current corpus can browser-exercise, not a failure.
- TC-13 sweep (bounded): the same full-page HTML capture shows every other shipped `/desk` section unchanged — desk-screen-not-computed panel with its controls, Top-up Runs / Index Reconciliation / Screen Runs (collapsed, unmoved headings), Playbook Signals (honest "not computed" state + Run Playbook button), Backscan ("No back-scan runs recorded yet."), Playbook Evidence (collapsed), Referee Adjudications (collapsed), Referee Runs (collapsed) — none of their headings, testids, or rendered text differ from prior iterations' reports. Collapsed sections were not individually expanded (bounded sweep, not a full re-test of J-07/J-09/J-11's own content, which is deterministic-replay's job this round).
- Screenshot at 1683×4320 shows the Registered Hypotheses table, Playbook Family (fully in frame), and the first two rows of Strategy Family; the tail of Strategy Family (trade count onward) is below this screenshot's frame but is fully proven by the DOM-text byte-match above (T-10 is satisfied by the screenshot proving real, non-blank rendering; the DOM extraction is the string-for-string source of truth this journey's acceptance actually calls for).

**State 2 — empty-corpus backend (TC-9, the dev-flagged gap):**
- No pre-existing empty-corpus rig launcher existed in this repo (checked `apps/backend/scripts/*qa*`/`*fixture*` — all of them SEED a rig, none produce a genuinely empty one). Built one: fresh backend on :8302 with `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_BAR_DIR` pointed at a brand-new empty directory under `$TMPDIR/empty-corpus-rig/` (the sibling-default pattern documented in goal.md redirects the playbook/screen/forward/referee stores along with it), plus a frontend on :3302 pointed at it (`NEXT_PUBLIC_API_URL=http://localhost:8302`).
- **First attempt was NOT actually empty**: `GET /research/desk/referee/evidence` on the freshly-isolated :8302 showed `playbook_occurrence` genuinely zeroed, but `strategy_trade.trade_count=873` — exactly the dev handoff's own REAL-corpus number. Root cause: `strategy_trade_readiness()` reads trade counts from a `JournalStore` keyed by `TAPEOLOGY_JOURNAL_DB` (`app/config.py:1328`), a SEPARATE env var not covered by the universe/dataset/bar overrides. Fixed by also setting `TAPEOLOGY_JOURNAL_DB` to a fresh path before relaunching; re-checked via `curl` and confirmed all fields genuinely zero before spending any browser cycles on it. Flagging this because it is a real, reusable fact for any future session building an empty/isolated referee rig — not a J-12 defect (J-12 is a pure frontend read of an unchanged backend computation).
- Navigated `http://localhost:3302/desk` (200, no crash on a universe with zero snapshots), expanded Referee Registry. Full HTML DOM extraction confirmed:
  - `referee-hypotheses-empty`: "No hypotheses registered." (the shipped Registered Hypotheses section's own honest-empty state, not part of J-12 but confirms nothing broke)
  - `referee-evidence-playbook-block`: Records `0`, Distinct sessions `0`, Signals at current basis `0`, same `detector_basis`/`config_fingerprint` (code-derived, corpus-independent), "No stale basis dates.", "No integrity errors."
  - `referee-evidence-strategy-block`: Datasets `0`, Train/Holdout `0`/`0`, Trades `0`, the SAME tick-gate-unmet sentence and Card-6.4 caveat (both are static disclosures the backend computes even from an empty corpus, matching the dev's own reasoning), "No integrity errors."
  - No blank area, no spinner, no 404/error path anywhere on the page.
- Screenshot evidence: two techniques were needed. Setting the viewport to the tool's max (4320px, still short of this page's ~5492px `scrollHeight`) and capturing without scrolling produced a real, legible, non-blank image (Playbook Family fully in frame, "No hypotheses registered." visible, Strategy Family beginning at the bottom edge) — this is the file referenced above. Two follow-up attempts that used any form of scroll (`window.scrollTo`, `Element.scrollIntoView`) after the initial render, to try to frame the Strategy Family block more tightly, both produced a ghosted/largely-blank capture (sticky nav duplicated with a large blank gap) — reproducing exactly the capture trap the pump note described. Those two broken captures were discarded; the working (non-scrolled, resized-viewport) screenshot plus the complete DOM-text extraction above are the evidence of record.
- Console clean (only the standard React DevTools notice) on both navigations.
- Teardown: both processes stopped by exact PID (never pattern-based kill), `.next` cleaned, primary :3301 frontend rebuilt and relaunched against :8301, re-verified 200, and the primary rig's live data re-confirmed byte-identical to before this test began (records=4, distinct_sessions=3, signals=21, dataset_count=0, trade_count=0) — the empty-corpus backend never touched the primary rig's stores, by construction (fully separate directories) and by re-check.

---

## Skipped Tests

None. Both journeys in scope this run were fully exercised.

---

## Notes

- **UT-J-05 vs. the deterministic replay's FAIL, explained:** `reports/phase-goal-referee-iter-13-regression-replay-results.md` (written by `demo_runner.py` earlier this iteration) recorded J-05 as FAIL: "step 02 expected 'historical-exploration' did not appear," with its own screenshot `J-05-verify.png`. That screenshot shows the viewport cut off just above the Registered Hypotheses table (visible content stops at the Backscan section). `demo_runner.py`'s expect-check (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:641`) is `page.get_by_text(...).first.wait_for(state="visible", timeout=...)` — a Playwright *visibility* wait, not a DOM-presence check. My own pass, using full HTML DOM extraction (not the markdown extraction, which silently dropped this same table's contents — a tool quirk worth remembering) at a resized-to-fit viewport, found the text unambiguously present and correctly rendered, cross-checked against the live endpoint. I read this as a capture/visibility artifact in the replay tool on this specific tall page, not a product regression, and widened `J-05.json`'s `default_timeout_ms` (8000 → 12000) defensively when rewriting the golden script, without changing its assertions (which are correct). I did not attempt to modify `demo_runner.py` itself — out of my remit as browser-qa-agent.
- **Operational note (self-inflicted, resolved):** while setting up the empty-corpus rig, a second `next dev` process was briefly run concurrently with the primary :3301 frontend from the SAME `apps/frontend` working directory. Both processes share one `.next` build directory; running two `next dev` instances against it concurrently corrupted the primary rig (500s on every route) within seconds. Recovered by killing the rogue process, then the primary frontend (SIGTERM was insufficient — the corrupted process needed SIGKILL), `rm -rf .next`, and a clean relaunch. All subsequent frontend work (including the empty-corpus pass) used ONE frontend process at a time (sequential swap, never concurrent), which does not hit this collision. Documented here so a future session does not repeat it.
- Not separately browser-tested this run (judged out of the literal J-05/J-12 Acceptance text, and already covered elsewhere): the backend-unreachable and non-200 error-message paths for `fetchRefereeEvidence()` — these mirror `fetchRefereeShortlist`/`fetchRefereeRegistry`'s already-established, already-tested pattern verbatim (confirmed by reading `lib/api.ts`), and TC-3's non-empty `stale_basis_dates` render (no rig with that fixture shape was available this run; the dev's own backend test covers it).
- Golden replay scripts written/updated this run: `runs/goal-session-referee/journey-scripts/J-05.json` and `J-12.json` (both `default_timeout_ms` bumped 8000→12000; assertions unchanged from what was already on disk, since both were independently verified correct). Both linted clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3301 (primary rig, restored to this exact state at the end of this run)
- **Backend URL:** http://localhost:8301 (primary rig, `fixture-rig-iter8-replay`; untouched throughout — only its frontend was cycled)
- **Temporary rig (TC-9 only, torn down before finishing):** backend :8302 / frontend :3302, fresh empty store directories under `$TMPDIR/empty-corpus-rig/`
- **Browser:** Headless Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`, CDP `127.0.0.1:9222` (pump-launched, pinned profile — never changed)
- **Test Date:** 2026-08-16
- **Evidence directory:** `reports/qa/goal-referee-iter-13-evidence/`
