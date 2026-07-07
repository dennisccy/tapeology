# goal-structure_ui-iter-4 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal was achieved and independently verified. This evidence-capture iteration set out to
photograph the populated J-03 Comparison render — the exact deliverable iter-3 skipped with services
down — and it did: `reports/qa/goal-structure_ui-iter-4-evidence/UT-04-finished-comparison.png` shows
the real populated state (both backtests `done`, side-by-side aggregates, per-class A/B/C
insufficient-sample chips, verbatim register lines, champion unchanged at `v1`/`default`, and the
honest `structure_tape` `n=0` → "no trades (n=0)"), and I confirmed the on-screen values match the
byte-match claims by opening the image myself. The frozen foundation held (both `apps/` diffs
byte-empty, `config_fingerprint` recomputes to `4d665603569b9dbf`), and every critical anti-goal is
verified in the actual code, not just asserted. The gaps are minor and forward-looking (no J-03
golden-replay script; one premature QA-lane report now superseded) and do not compromise J-03 passing
or the goal — iter-3's blocking evidence gap is fully closed.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): Frozen foundation independently confirmed**
`git diff --stat -- apps/backend` and `-- apps/frontend` are both byte-empty on branch
`goal/structure_ui` (verified directly, not read from the handoff). `config_fingerprint` recomputes
live to `4d665603569b9dbf` via `.venv/bin/python -c "from app.config import CONFIG;
print(CONFIG.config_fingerprint())"` — exact match to the pinned J-04 value. No backend edit exists,
consistent with the "no new backend computation or endpoint" anti-goal.

### Frontend Findings

**F1 — OBSERVATION (no change needed): "UI recomputes nothing" (trap T10) verified in code**
The values I saw on screen are read verbatim from the payload with no client-side math:
`apps/frontend/app/structure/page.tsx:447-448` renders `{String(agg.net_r)}` / `{String(agg.net_usd)}`
(raw pass-through — no `toFixed`, no rounding, which is precisely why the screenshot preserves
full-precision floats like `-16.000000000001137`). `page.tsx:474-475`'s `formatNullableAggregateField`
returns the literal `"no trades (n=0)"` **only** when the API field is `null`, never fabricating a
`0`. `page.tsx:450` drives the `insufficient sample (n < 5)` chip directly off the API boolean
`agg.insufficient_sample`. Grep found no `Math.`/`reduce(`/aggregation in the file.

**F2 — OBSERVATION (no change needed): "UI never promotes / never writes the ledger" verified in code**
Every ledger/champion reference in the frontend is a read: `apps/frontend/lib/api.ts:827` is a plain
`GET /research/pnl/ledger`; `page.tsx` only holds those read results in state and renders labels.
`page.tsx:1027-1028` carries the explicit invariant comment ("This view starts a research job; it
moves the champion NEVER and writes nothing to the ledger."). No `POST`/`set_champion`/`promote`/
ledger-write call exists in `app/structure/` or `lib/`. `git status` shows zero tracked data-file
mutation. The champion badge reads `v1`/`default` in every screenshot.

**F3 — OBSERVATION (carry-forward, out of scope): PriceChart.tsx latent z-index occlusion (F2 from iter-1)**
`apps/frontend/components/PriceChart.tsx` (Cockpit/J-04) still shares the latent empty-state z-index
occlusion that was fixed on the sibling `StructureChart.tsx` in iter-1. This iteration touches neither
the Cockpit nor `PriceChart.tsx` (zero frontend diff), so it is not a regression introduced here and
is correctly deferred to a future Cockpit-touching iteration per the spec's Out of Scope list.

### Test Findings

**T1 — GAP (documented, not fixed — outside this iteration's DoD): no J-03 golden-replay script**
`reports/phase-goal-structure_ui-iter-4-ui-test-results.md:221-226` documents that `J-03.json` was
deliberately not written: the Comparison flow's mandatory dataset picker is a native `<select>`, and
the replay runner's `fill` action uses Playwright's `.fill()`, which does not drive `<select>`
elements. This is an honest, disclosed best-effort skip, and it is **not** a DoD miss — the DoD
requires browser-qa evidence (supplied and verified), not a replay script. The forward cost worth
recording: J-03 has no cheap deterministic-replay regression path, so each future iteration must
re-verify it with a full browser pass (as this one did). `J-01`/`J-02` replays were left intact and
`J-04.json` was added (lint-clean).

**T2 — OBSERVATION (superseded, no action): QA-lane report gave a premature PASS**
`reports/qa/goal-structure_ui-iter-4-qa.md` carries "**Verdict:** PASS" while its own Step 7
(lines 157-164) states the primary deliverables TC-05–TC-09 were "Awaiting backend job completion"
and "Screenshots will be captured once results are available," and its listed screenshots
(`UT-01-structure-page-loaded.png`, etc.) no longer exist — they were overwritten by the
browser-qa-agent's later, thorough 11:00–11:26 run. Net outcome is correct because the DoD requires
`browser-qa-agent` evidence specifically, and that independent run (`ui-test-results.md`, 18/18 PASS)
IS the authoritative, DoD-satisfying artifact. Flagged only as an evidence-discipline note for the QA
lane; it does not affect the audit verdict.

**T3 — OBSERVATION (explained, no action): evidence set has 10 unique images across 14 filenames**
`md5sum` shows `UT-01`=`UT-02`=`UT-17`, `UT-12`=`UT-13`, and `UT-04`=`UT-18` are byte-identical. This
is fully explained by the browser-qa-agent's documented capture workaround
(`ui-test-results.md:197-213`): the viewport was sized tall (1400×2800) so the whole page fits at
`scrollY=0` (the one scroll position proven free of a Chrome-MCP `position: sticky` capture artifact),
so a single full-page screenshot legitimately contains multiple asserted sections. I confirmed each
image genuinely contains its asserted state (e.g. `UT-12` really shows the populated candlestick chart
+ 6 confluence zones; `UT-04` really shows the finished comparison). Not fabrication.

---

## 3. Domain Assessment

The core honesty properties this session exists to prove are genuine, and I verified them against the
ground-truth screenshots and the source, not the handoff prose:

- **Populated J-03 is real and byte-faithful.** `UT-04-finished-comparison.png` shows v1 (n=1,
  net R `-0.16000000000001136`, net $ `-16.00000000001137`, win_rate `0`, max_dd
  `0.16000000000001136`) and structure_tape (n=0, win_rate/max_dd = "no trades (n=0)"), with all six
  per-class rows carrying the amber "insufficient sample (n < 5)" chip and both cards showing the
  register "simulated — assumed fees/slippage — not indicative of live results." The browser-qa-agent
  obtained the byte-match by instrumenting `window.fetch` (read-only) to recover the exact backtest
  ids this run created, then diffing each `GET /research/backtests/{id}` field-by-field against the
  on-screen text (`ui-test-results.md:69-85`). The full lifecycle is evidenced: `UT-03-queued-transient`
  shows the transient "Running…"/"Queued…" frame, `UT-04` shows `done`.
- **The keyless non-survivor is honest, not a manufactured green.** structure_tape's `n=0` is rendered
  as an explicit "no trades (n=0)" (never a bare `0`), and the code path confirms this is null-driven
  (`page.tsx:474-475`), not fabricated. This preserves the goal's central honesty stance.
- **J-01 regression is genuinely populated and un-occluded.** `UT-12-populated-chart-zones.png` shows
  a real 9-candle chart with labelled dashed S/R lines and 6 confluence zones, no empty-state overlay —
  iter-1(a)'s z-index fix holds. The agent staged the project's own committed bar fixtures into the
  gitignored `apps/backend/.data/bars/`, ran the check, and cleaned up; I confirmed `.data/bars/` is
  now empty and no fixture/source leaked into git — an honest, transparently-documented technique
  (mirroring iter-1), not a persistent data mutation.
- **Frozen foundations + no-promotion invariants hold** as detailed in B1/F2.

The one nuance the agent surfaced honestly (`ui-test-results.md:128-138`): with bars staged, the
*largest* dataset yields `structure_tape n=3` real trades — so "structure_tape always arms zero
trades" is a property of the specific keyless bars-absent default, not an absolute. Both the non-zero
and the `n=0` outcomes render honestly. This is a correct, non-fabricated disclosure that strengthens
rather than weakens the evidence.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found; all findings are GAP/OBSERVATION level and are either
outside this iteration's DoD (T1), superseded (T2), explained (T3, F3), or confirmatory (B1, F1, F2).
Applying any of them would be scope creep on a zero-diff, frozen-foundation iteration.

---

## 5. Recommended Next Step

**Proceed — this is a clean GOAL_ACHIEVED candidate for the evaluator.** J-03 flips `unknown` →
`passing` on independent, populated, byte-matched browser-qa evidence, and J-01/J-02/J-04 are
re-verified green, so all four Must-have journeys are green. iter-3's standing evidence gap (which
drove its CLOSURE-FAIL / UX-REGRESSION-WARN / audit PASS_WITH_GAPS) is fully closed; ux-regression has
already returned UX-REGRESSION-PASS. The remaining pipeline gate is phase-closure-auditor, which runs
after this audit and should now return CLOSURE-PASS. Carry forward two non-blocking notes for a future
Cockpit-touching iteration: (a) `PriceChart.tsx`'s latent z-index occlusion (F3), and (b) the absence
of a J-03 golden-replay script (T1) — meaning J-03 will need a full browser pass each iteration until
the replay runner can drive a native `<select>`.
