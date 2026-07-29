# goal-desk-iter-15 Audit Report

**Date:** 2026-07-29
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-11's product substance is real and correct: `history_sessions`/`history_start` are derived inside
the one ascending `merged_bars` walk the row builder already performed, they match the canonical
merged daily series exactly (I re-derived all 63 rows of the recorded screen independently — zero
mismatches), skip rows and legacy rows honestly carry nothing, and `/desk` renders the split
visibly. One DEFINITION-OF-DONE item was **claimed but structurally absent**: the `[NEW]`-flagged
demo-narrator walkthrough never ran — the authored `demo.json` embedded JavaScript regex literals,
so `demo_runner.py` could not parse it, the lane recorded `SKIPPED` with zero screenshots, and QA
marked TC-11 PASS against the wrong file. That is fixed and re-recorded during this audit
(`RECORDED`, 9 steps, 9 screenshots, zero soft notes). Residual items are test-organization and
evidence-labelling gaps only.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): the derivation is a walk-position count, and that is
provably the right count.**
`apps/backend/app/research/desk_screen.py:270-278` counts bars as it walks and returns at the
`basis_as_of` match, so `history_sessions` is the walk POSITION of the basis bar, not a filtered
"at or before" count. Those are only the same thing if `merged_bars` is strictly ascending with
unique timestamps. I verified that it is: `bars.py:538` builds the fold as
`merged = [by_ts[ts] for ts in sorted(by_ts)]` over a `dict` keyed on `ts`, and price-less rows are
excluded from the fold (`bars.py:482-493`, the era-desk-iter-4 audit B1 rail). So the position count
is exactly the at-or-before count, over exactly the same rows `GET /research/candles` serves. No
defect — recorded because the equivalence is load-bearing and is not asserted anywhere as an
invariant of `merged_bars` itself.

**B2 — OBSERVATION: "history" measures the DAILY series only, while the wall is built from
1h/4h/1d/1w levels.**
`tradability.py:406-422` computes the bands through `_PriorSessionBarView` over EVERY timeframe;
`history_sessions` counts `1d` bars only. The rendered copy makes no false claim — the cell is a
bare count and a date (`page.tsx:338`), and the column header is the single word `history` — so
nothing on screen overstates it. Only goal.md's own prose ("how much completed history its wall was
measured over") is looser than what is measured. No product change warranted; noted so a later
iteration does not build a threshold on a number that describes one timeframe.

**B3 — verified, not a finding: no-lookahead, append-only and rank-key all hold.**
Only bars at or before the row's own `basis_as_of` are counted (the walk returns at the match), so
the count can never see a bar the wall could not. `_row_rank_key` (`desk_screen.py:244`) is
byte-unchanged and reads none of the new fields, so the rank order structurally cannot move. Legacy
snapshots are untouched: I re-read `screen-2026-07-29-ce0d82b8e9bf` from disk — 63 ranked rows,
**zero** carrying either key (absent, not `null`). Re-running the demo lane twice during this audit
wrote no new snapshot (`.data/screen/` still holds the same 6 files with unchanged mtimes).

### Frontend Findings

**F1 — OBSERVATION: `DeskScreenRow` declares the new fields as required (`number | null` /
`string | null`), but a legacy row omits them, so the runtime value is `undefined`.**
`apps/frontend/lib/types.ts:819-820`. Every consumer uses the loose `== null` check
(`page.tsx:244`, `page.tsx:336`), which catches `undefined`, and the comment block at
`types.ts:800-806` documents the contract explicitly. This mirrors the `basis_as_of`/
`basis_age_days` precedent the spec told the dev to follow, so changing it now would be a
cross-cutting refactor, not this iteration's work. Left as-is deliberately.

**F2 — GAP: the TC-09 evidence screenshot does not show a tooltip.**
`reports/qa/goal-desk-iter-15-evidence/TC-09-tooltip.png` is byte-for-byte the same view as
`TC-08-history-column.png` — a native HTML `title` tooltip is never painted into a screenshot. The
underlying check is nonetheless genuinely verified, by a stronger method than a screenshot: the LLM
browser lane read the anchor's `title` attribute directly (`ui-test-results.md` UT-03 records the
full string, `... basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 27 sessions from
2026-06-15T04:00:00.000000Z · ...`) and confirmed the click still navigated to
`/structure?symbol=HONA&asof=...`; `test_desk_hover_tooltip_guard.py` additionally pins
`row.history_start` as a required needle in the tooltip builder. The file NAME overpromises; the
verification is sound.

### Test / Artifact Findings

**D1 — IMPORTANT (fixed): the `[NEW]`-flagged demo-narrator walkthrough — DEFINITION OF DONE item 5
— never ran.**
`reports/phase-goal-desk-iter-15-demo.json` contained three JavaScript regex literals in place of
JSON strings (`{"role": "link", "name": /history.*sessions/}` at line 40, and the same at lines 52
and 76). `json.loads` therefore failed at line 40 column 72, `demo-phase.sh` recorded
**`Demo Verdict: SKIPPED`** with an empty Captured-Steps table, and neither
`reports/demo/goal-desk-iter-15/` nor `reports/phase-goal-desk-iter-15-demo-script.md` existed at
all. This iteration was dispatched at `full` depth *specifically* so this lane would run before the
evaluator scores it (the spec's own Full-trigger rationale, and the binding iter-12 `ESCALATE`
lesson) — so a silently skipped lane defeats the reason the depth was chosen.

Three of the eight authored steps were also semantically wrong independent of the parse error: step
3 clicked a `role: link` named "history…" (the history cell is a `<td>`; the row's only link is the
drill-in anchor, whose accessible name is `Open <SYM> in Structure as of …`), and steps 5 and 7
narrated a hover and the legacy fallback while their actions did something else entirely.

Fix applied — see §4. The repaired script is valid JSON (`validate_script` → `[]`), every action
now matches its own narration, and it is deliberately read-only (no `Run Screen`/compute trigger,
so re-recording can never write a snapshot).

**D2 — GAP: QA marked TC-11 PASS against the wrong artifact.**
`reports/qa/goal-desk-iter-15-qa.md:56` records TC-11 as PASS with the evidence "File
`runs/goal-session-desk/journey-scripts/J-11.json` exists and is valid JSON". TC-11 is about the
demo-narrator WALKTHROUGH (`reports/phase-goal-desk-iter-15-demo.json` + its gallery), not the
golden replay script. The two are different artifacts written by different lanes; checking the
existence of one while the other was broken is what let a `SKIPPED` lane through a `PASS` QA
verdict. The test-plan's own TC-11 pass criteria ("Screenshots show the history column with
values", "at least one row with `history_sessions ≤ 60` and one with `≥ 400` both present") were
never evaluated. After the D1 fix the row's verdict is now true on the merits; the mis-citation is
recorded here because it is a repeatable QA failure mode, not a one-off.

**T1 — GAP: the MCP `desk_screen` proxy pass-through check the spec listed IN SCOPE was not
written.**
The spec's Backend IN SCOPE bullet asks for "an MCP `desk_screen` proxy pass-through check" inside
`apps/backend/tests/test_desk_screen.py`; no such test exists there. The dev flagged the omission
honestly in the handoff's Known Issues rather than hiding it, and the reviewer filed it MINOR. I
verified the substitute claim rather than accepting it:
`tests/test_mcp_server.py:327-370`'s populated-state test asserts
`result.content[0].text.encode("utf-8") == rest.content` — a whole-body byte comparison that is
genuinely field-agnostic, so a new row field cannot break it. The property is therefore proven; the
literal spec item is not. GAP, not IMPORTANT — no product behaviour is unverified.

**T2 — OBSERVATION: the QA report's TC-07 row cites the wrong evidence.**
`goal-desk-iter-15-qa.md:52` marks TC-07 (candles cross-check) PASS with the Actual "MCP proxy
tests pass (generic payload byte-identity, field-agnostic)" — which is TC-07's neighbour, not
TC-07. The real test does exist and does pass
(`test_desk_screen.py::test_aapl_row_history_cross_checks_against_get_candles`, which filters
`GET /research/candles`'s own response to bars at/before `basis_as_of` and compares both fields). I
also proved the property independently on REAL data rather than the fixture: for all 63 ranked rows
of `screen-2026-07-28-ac07c9581a4f`, re-deriving the count and earliest timestamp straight from
`BarStore.merged_bars(symbol, "1d")` reproduced `history_sessions`/`history_start` exactly — 0
mismatches. Single source of truth holds.

**T3 — verified, not a finding: the test block is tight, not loose.**
TC-1/TC-2 assert exact golden values (`5`, `450`) and exact ISO timestamps, not ranges; the
off-by-one edge (`history_sessions == 1` when the basis IS the first bar) is covered explicitly;
TC-6 is a real guard, comparing a full screen walk's per-symbol `merged_bars(…, "1d")` count against
`compute_tradability` run alone and asserting the delta is exactly `+1` — a second walk would make
it `+2`. TC-5's skip-row assertions were added to the two EXISTING skip tests rather than as
new isolated tests, so they cannot silently pass on an empty collection.

### Independent verification I ran (not taken from any handoff)

| Check | Command / method | Result |
|---|---|---|
| Full backend suite | `pytest tests/ -q` (exit 0) | 1418 passed, 8 skipped, 0 F/E (counted from the progress bar — the summary line is genuinely absent in this environment, reproducing the dev's disclosure) |
| Targeted | `pytest tests/test_desk_screen.py tests/test_desk_hover_tooltip_guard.py tests/test_copy_discipline.py tests/test_mcp_server.py -q` | 117 passed |
| Fingerprint | `Config().config_fingerprint()` | `08e471b10130e1e2` |
| MCP surface | `len(app.mcp.TOOL_NAMES)` | `17` |
| Real recorded screen | direct JSON read of `.data/screen/screen-2026-07-28-ac07c9581a4f.json` | 63 ranked rows all carry both fields; 38 skip rows carry neither; no nulls; `history_start <= basis_as_of` on every row; span 27…501 (1 row ≤60, 57 rows ≥400) |
| Legacy screen | direct JSON read of `screen-2026-07-29-ce0d82b8e9bf.json` | 63 ranked rows, both keys ABSENT on every one |
| SSOT | re-derived both fields for all 63 rows from `BarStore.merged_bars` | 0 mismatches |
| Append-only | `.data/screen/` before vs after two demo re-runs | 6 files, unchanged mtimes |

---

## 3. Domain Assessment

The core domain logic is correct and, unusually for a disclosure journey, is correct for the right
reason. The value being disclosed is not a new statistic invented beside the existing computation —
it is a byproduct of the walk the row builder already had to perform, read off the same canonical
accessor (`BarStore.merged_bars`) that `tradability._select_daily_series` and `compute_levels`
themselves read. That is what makes the single-source-of-truth claim structurally true rather than
coincidentally true, and it is why my 63-row re-derivation from the store matched byte-for-byte.

The honesty discipline this era is built on holds throughout. A legacy row does not get a `0`, a
`null`, or a blank — it gets `"history not recorded in this snapshot"`, and I confirmed that state
renders on a REAL pre-iteration snapshot, not only in a unit test (demo `step-06.png`: all history
cells show the fallback while the basis column beside them still shows real per-row values). A skip
row gets no history cell at all, because it is in a different table that structurally never had
one. Nothing is backfilled on read.

The copy stays inside the era's descriptive-measurement rail: a count and a date, no "enough
history", no confidence score, no threshold, and nothing in the rank key. `distance_bps`/
`band_score`/`price_low`/`price_high` and the `(band_class, distance_bps, band_score, symbol)` tuple
are byte-unchanged, so the disclosure genuinely discloses and does not quietly become a filter.

The one conceptual softness (B2) is that "history" here means daily-bar depth, while a wall is built
from four timeframes. The UI never claims otherwise, so this is a naming looseness in the goal
prose rather than a misleading surface — but it is exactly the kind of number a future iteration
might be tempted to threshold, and it would be the wrong number for that.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-desk-iter-15-demo.json` | Rewrote the demo-narrator walkthrough: replaced the three JavaScript regex literals that made the file unparseable with plain JSON string targets, realigned every step's action with its own narration (the previous steps 3/5/7 narrated a hover or the legacy fallback while clicking something else), kept the script strictly read-only (no compute trigger), and added steps 8–9 so the gallery captures the short/long split in one frame. Documented the repair, the read-only property and the capture geometry in the script's own `notes`. |
| 2 | Important | `reports/phase-goal-desk-iter-15-demo-results.md`, `reports/phase-goal-desk-iter-15-demo-script.md`, `reports/demo/goal-desk-iter-15/step-01..09.png` | Regenerated by re-running the lane (`./scripts/automation/demo-phase.sh goal-desk-iter-15`, cached-script path, no model dispatch). |

**Post-fix verification (evidence, not assertion):**

1. `validate_script(json.loads(...))` → `[]`, 9 steps, `new` flags `[False, True, True, True, True,
   True, True, False, True]`.
2. `./scripts/automation/demo-phase.sh goal-desk-iter-15` → exit 0,
   `[demo_runner] recorded 9 step(s) → reports/demo/goal-desk-iter-15 (verdict: RECORDED)`.
   `RECORDED` (not `RECORDED_WITH_NOTES`) means every action succeeded AND every `expect` was
   satisfied — no soft notes.
3. Screenshots inspected, not just counted: `step-06.png` shows the legacy `2026-07-29` snapshot
   with every history cell reading `history not recorded in this snapshot` beside real basis
   values; `step-09.png` shows the latest `2026-07-28` snapshot with BRK-B `history 500 sessions ·
   from 2024-07-25` and HONA `history 27 sessions · from 2026-06-15` legible in the SAME 1280×800
   frame — the ≤60/≥400 split TC-11 asks for.
4. Scope re-checked with `git status --porcelain`: **zero** tracked source, test, or spec files were
   modified by this audit. The only changes are the four untracked demo artifacts above.
5. No new finding introduced: the script triggers no compute, and `.data/screen/` still holds the
   same 6 snapshot files with unchanged mtimes after two full re-runs — the append-only rail is
   intact.
6. Handoff claims invalidated by this fix: none. Neither the dev nor the frontend handoff claimed
   the demo lane; they correctly left it to the downstream lane.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator. J-11's acceptance is now fully evidenced end to end: backend
derivation (1418-test suite green, fingerprint pinned, 17 MCP tools), single source of truth proven
against the real store on all 63 rows, the ≤60/≥400 browser screenshot (`UT-02-result.png`,
`TC-08-history-column.png`), the tooltip's full-precision `history_start` read from the live DOM
(UT-03), the honest legacy fallback on a real pre-iteration snapshot, all eight required-still-
passing journeys replayed green, and — after this audit's fix — a `[NEW]`-flagged demo-narrator
walkthrough that actually recorded.

Two small items to carry forward rather than fix now (both GAP-level, both deliberate):

- Write the MCP `desk_screen` pass-through assertion the spec listed IN SCOPE (T1) — a few lines
  seeding a `ScreenStore.record()` carrying the new fields and diffing MCP against REST. The
  property is already proven generically; this closes the literal item.
- The QA lane should verify TC-11 against `reports/phase-goal-desk-iter-15-demo*.json/.md` and the
  gallery directory, not against `runs/goal-session-desk/journey-scripts/J-11.json` (D2). A
  `Demo Verdict: SKIPPED` in the demo-results file should be a hard QA blocker whenever the spec's
  DoD names a `[NEW]`-flagged walkthrough — that single check would have caught this iteration's one
  real gap without an audit pass.
