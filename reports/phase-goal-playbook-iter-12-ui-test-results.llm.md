# Phase goal-playbook-iter-12 — UI Test Results

**Phase:** goal-playbook-iter-12
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode dispatch: this run tests EXACTLY J-11 with a live Chrome MCP pass. J-01, J-02, J-03,
J-07, J-08, J-09, J-10 are explicitly out of scope for this run — a deterministic golden replay
verifies them separately (see `reports/qa/goal-playbook-iter-12-evidence/J-0{1,2,3,7,8,9}-verify.png`
and `J-10-verify.png`, already present from that separate replay pass; not touched or re-verified
by this report).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-11 | Every evidence cell states the basis of its own n | happy-path | P1 | On `/desk`, the Playbook Evidence section shows a new basis line beside "Built from signature:" and at least one visible cell row shows `n_unmeasured > 0` beside its own `n` | Basis line renders exactly `GET /research/desk/playbook/evidence`'s `basis` block, byte-identical to the raw API response; cell `open_high_break / long / 1m` renders `n=0, n_unmeasured=15` (signal) and `n_baseline=0, n_unmeasured=11` (baseline), also byte-identical to the API | PASS | `reports/qa/goal-playbook-iter-12-evidence/UT-J-11-result.png` |

---

## Passed Tests

### UT-J-11 — Every evidence cell states the basis of its own n
**Verdict:** PASS
**Evidence:** `reports/qa/goal-playbook-iter-12-evidence/UT-J-11-result.png`

Steps executed (per `docs/goal.md` J-11's own numbered steps / Acceptance line, sliced into
`runs/goal-session-playbook/iter-12/goal-slice-bqa.md`):

1. Navigated Chrome MCP to `http://localhost:3301/desk` (the scoped fixture rig frontend) and
   waited for `Built from signature:` to appear (confirms the Playbook Evidence section finished
   its async GET).
2. `extract`ed the full text content of `[data-testid="desk-evidence-section"]` and confirmed,
   verbatim:
   - The existing signature line is present and byte-unchanged: `Built from signature:
     486619a733a8aa92`.
   - A NEW basis line immediately follows: `Basis: 5 records pooled from 2026-06-22, 2026-06-23,
     2026-06-24, 2026-06-25, 2026-08-07 (created 2026-08-12T04:43:10.381419Z ..
     2026-08-12T04:43:28.553773Z)` — cross-checked byte-for-byte against a direct `curl` of
     `GET http://localhost:8301/research/desk/playbook/evidence` taken moments earlier (same
     `basis.dates`, `basis.n_records: 5`, `basis.created_span`), so the rendered line is a pure
     pass-through of the served `basis` block, not a client-computed value.
   - The updated `EVIDENCE_REGISTER` copy is present and names the unmeasurable class, the
     baseline's own `n_truncated`/`n_unmeasured`, `n_sessions`, and the basis block — no
     probability/expectancy/edge/significance language observed.
   - The cells table's first row (`open_high_break | long | 1m`) reads, in order: signal
     `n=0, trunc=0, unmeas=15, sess=4`; baseline `n=0, trunc=0, unmeas=11, sess=4` — matching the
     same `curl`'d JSON cell exactly (`signal.n_unmeasured: 15`, `signal.n_sessions: 4`,
     `baseline.n_truncated: 0`, `baseline.n_unmeasured: 11`, `baseline.n_sessions: 4`). This cell
     satisfies the Acceptance line's "at least one visible cell whose `n_unmeasured` is greater
     than zero beside its own `n`" literally (`n=0` and `n_unmeasured=15` are both rendered, side
     by side, in the same row). A backend-side sweep found 21 such cells across 7 distinct
     (setup, side) pairs on this fixture rig; this row is simply the first one in DOM order.
   - Confirmed via `get_console_messages`: no console errors or warnings (only the standard React
     DevTools info line).
3. Captured the acceptance-state screenshot. Direct scroll-then-screenshot (`scrollIntoView` and
   also the tool's native `scroll` action) produced a **reproducibly blank frame** once the
   Playbook Evidence section was brought into view by scrolling — a headless-Chrome rasterization
   quirk on this tall page (`document.body.scrollHeight` 12041px) that is independent of the app
   (confirmed `document.visibilityState === "visible"` throughout, i.e. not the previously-known
   live-chart `hidden`-tab throttle; a screenshot at `scrollY=0` rendered correctly every time, so
   the app itself paints fine — only a screenshot taken while scrolled deep down the page came
   back blank, both via JS `scrollIntoView` and the tool's own `scroll` action). Worked around by
   setting the browser viewport to `1280×4200` (`set_viewport`) so the target section fell inside
   the natural, unscrolled first paint, screenshotting that, then cropping the saved PNG locally to
   the Playbook Evidence region (`reports/qa/goal-playbook-iter-12-evidence/UT-J-11-result.png`).
   Viewport was reset to `1280×1400` afterward. The resulting screenshot visibly shows the "Playbook
   Evidence" panel heading, the "Built from signature:" line, the new "Basis: 5 records pooled
   from …" line directly beneath it, the updated register paragraph, the widened table header
   (`SIGNAL` block now `n / trunc / unmeas / sess / median / p25 / p75 / mean`, `BASELINE` block
   mirroring it), and the `open_high_break / long / 1m` row with `unmeas: 15` beside `n: 0` on the
   signal side and `unmeas: 11` beside `n: 0` on the baseline side.
4. Independently cross-verified via the project's own deterministic Playwright runner (not just
   the Chrome-MCP session): wrote `runs/goal-session-playbook/journey-scripts/J-11.json` and ran
   `python3 scripts/automation/lib/demo_runner.py --mode verify --base-url http://localhost:3301
   --scripts-dir runs/goal-session-playbook/journey-scripts --journeys J-11` → `1 journey(s), 0
   failed (verdict: PASS)`, a second, independent browser engine confirming the same result.
5. Confirmed no side effects: `GET /research/desk/playbook/evidence` re-`curl`'d after the whole
   pass returns the identical `basis` block (`n_records: 5`, same 5 dates, same `created_span`) —
   nothing was computed, recorded, or mutated by this browser pass. No compute/backscan/Run
   Playbook/Run Screen control was ever clicked.

Every shipped `/desk` section observed in the full-page screenshot (Desk screen panel, Top-up
Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, Back-scan Runs, Playbook
Evidence) rendered with its own shipped content and no error banner — consistent with "every
shipped `/desk` section still renders as shipped in the same pass," though per this run's lean-mode
scope only J-11 itself was exercised as a full test case; the other sections were incidentally
visible, not independently step-verified here (that is the deterministic replay's job for
J-01/02/03/07/08/09/10).

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend was running (`http://localhost:3301` → 200) and Chrome MCP was available
(CDP `127.0.0.1:9222` healthy throughout).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 — confirmed the **scoped fixture rig**, not the
  operator's real store: `GET /research/desk/universe` returns snapshots with `source_url`
  values `"fixture-rig"`, `"fixture-rig-iter7"`, `"fixture-rig-iter8"`, `"fixture-rig-iter8-replay"`
  (members `DECOR`, `RTAAA`, `DTAAA`, `BSCAN`, `OHB01..12`, `CALDR`, `OLBRK`, `JBEXP`, `DBIMP` —
  clearly synthetic fixture tickers, not real symbols). `GET /research/desk/playbook/evidence` on
  this rig pools 5 records across dates 2026-06-22/23/24/25 and 2026-08-07 (signature
  `486619a733a8aa92`), distinct from the dev handoff's real-corpus numbers (4 dates, signature
  `24a...`-style not shown) — confirming this run never touched the operator's real
  `apps/backend/.data/` store.
- **Browser:** Chrome via MCP (headless, CDP `127.0.0.1:9222`, pinned profile — not changed) +
  independent Playwright verify pass (`demo_runner.py --mode verify`) for the golden script itself.
- **Test Date:** 2026-08-12
- **Evidence directory:** `reports/qa/goal-playbook-iter-12-evidence/`
- **Golden replay script written:** `runs/goal-session-playbook/journey-scripts/J-11.json`
  (lint-checked with `demo_runner.py --mode lint`, then live-verified with
  `demo_runner.py --mode verify` against `http://localhost:3301` — both passed). Asserts the
  static `"Basis:"` label text (mirrors `J-09.json`'s own `"Built from signature:"` convention)
  and the structural presence of the new `[data-testid="desk-evidence-signal-n-unmeasured"]` cell,
  deliberately NOT the specific dates/counts/hash rendered today — those are fixture-rig data that
  R-3.3 (this session's own ruling, provoked by `J-10.json`'s step-6 rewrite) warns will drift the
  next time the scoped fixture rig is rebuilt, which would make a value-pinned assertion a false
  negative rather than a real regression signal.
- **Servers left healthy at handoff:** `:3301` → 200, `:3301/desk` → 200, `:8301/health` →
  `{"status":"ok"}`, Chrome CDP `:9222` → 200. Browser viewport restored to `1280×1400`.
