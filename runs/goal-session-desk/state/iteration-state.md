# Iteration State — desk

**After iteration:** 27 · **Date:** 2026-07-31 · **Verdict:** CONTINUE

## Journeys

17 passing (J-01..J-17) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` — 17 total (merged results 17/17 PASS). Only J-17 carries `evidence_makeup: true` (film owed; behaviour proven). No `pending_infra`. All 17 `spec_hash` values match the current `docs/goal.md`.

## Active blockers

- **J-17's `[NEW]`-flagged walkthrough — the ONLY open item, capture-lane owned.** A film exists (`reports/demo/goal-desk-iter-27/`, `RECORDED_WITH_NOTES`) but shows none of the journey: all 5 frames share md5 `dd3486a6bede477c9d9bb5475aa5bd27` (also equal to 8 `J-*-verify.png` files), and `step-02.png` is the AMBIENT `/desk` at top scroll with Top-up Runs not in frame. Cause: `reports/phase-goal-desk-iter-27-demo.json` has `base_url http://localhost:3301`, while the populated run existed only on the scoped rig `:3391`/`:8391`, torn down at 00:28 — one minute before the narrator ran at 00:29. FIX (spec must state both): keep the scoped rig alive until the demo step finishes, and set the film's `base_url` to the scoped frontend port. Frames must show the 4-outcome counts line, the tail-vs-full-lookback line, and ≥1 failed pair's `requested_window`; every target names ONE row.
- BOUNDED: iter-28 is the LAST capture retry the evaluator will request. If it fails again, drop the film to the owner's optional track and propose the finish on existing evidence.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 27: CONTINUE — rebuild landed (chunks carry inlined `localhost:8301`), 16/16 goldens green with zero edits, J-17 re-proven on a fresh scoped rig in one 1440×900 frame the evaluator opened; `08e471b10130e1e2`, 17 tools, 136 targeted tests exit 0, `.data` untouched, COHERENCE-PASS, scan CLEAN — but the film (this run's whole purpose) recorded the wrong page.
- iter 26: CONTINUE — J-17 built and proven number-for-number, but `Depth: full` was demoted to `lean`, which records no film at all.

## Do not redo

- **J-17 is BUILT and verified twice** — `_pair_window`'s three cases, the `unchanged` 409 outcome, the four additive per-pair fields, `/desk`'s counts + tail-vs-lookback line + per-failed-pair `requested_window` + the `WINDOW_BASIS_NOT_RECORDED` fallback. The ONLY gap is the film.
- **The `.next` rebuild is DONE** (inlined `localhost:8301`; the lone `localhost:8000` literal is `lib/config.ts`'s dead `??` fallback, not a defect). Never rebuild the SHARED `apps/frontend/.next` for a scoped rig — give it its own copy/`distDir`.
- **`journey-scripts/J-17.json` EXISTS** (written iter-27, linted + verified against ambient) as an honest partial proxy on the ambient legacy run. Do not delete or "fix" it to chase the scoped counts — no durable store can reproduce them.
- **The single existing-test edit is RATIFIED** (`test_desk_topup_compute.py:1092`, 4-key → 8-key set equality — widened, not relaxed). Do not revert it; do not edit any other pre-existing assertion.
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`, `flex-nowrap` badges). No width re-tuning, no 14th column; `band `/`opposite ` in-cell prefixes MUST stay (goldens pin them). Never script a `click` on a cell inside a `/desk` ranked or skipped row — the stretched `absolute inset-0` anchor makes it impossible; use `expect`-only.
- Zero diff stays law (re-verified iter-27, product tree byte-identical to `f6968e0`): `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `routes.py`, `meta.py`, `mcp/__init__.py`, both charts, the 5 guard test files; pin `08e471b10130e1e2`; 17 MCP tools; do not edit `docs/goal.md`. Evidence capture stays READ-ONLY on the ambient store. Accepted non-defects: 2/100 rows at 63 px, replay-frame duplication (16 files → 3 images), iter-25's optional film-wording note, goal.md's stale host-mask paragraph.
