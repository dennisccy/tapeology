# goal-playbook-iter-10 Execution Plan

Era-closing consolidation pass for Era B2 "The Playbook" (`docs/goal.md`'s R-3 ruling). No new
detector, no new journey, no new `Config` field, `config_fingerprint` stays `08e471b10130e1e2`.
Fully aligned with `docs/goal.md` (R-3.3 scopes exactly this) and builds on the shipped 10-journey
era (iter-9 dev handoff) without duplicating any of it. No scope drift found.

## What to Build

**A. Spec catch-up, doc-only, zero code diff (R-3.2(a)/(c)/(d)/(e)):**
- `docs/playbook-detector-spec.md` §3.8 Caps line (mirrors §3.9 by the file's own "mirror"
  convention -- one edit covers both): rewrite to the shipped reading, "the first pivot pair, in
  chronological `(p1, p2)` order, whose full formation validates AND triggers" -- already
  `_find_double_extreme`'s own docstring (`desk_playbook_detect.py:1310-1314`, confirmed live).
- §3.3 body + §1's `PLAYBOOK_JUMP_MIN_MULT` constants-table row: annotate that the BOOK 1.5x
  ratio gate is mathematically dominated by `PLAYBOOK_JUMP_MIN_MOVE_MBR`/`PLAYBOOK_BASE_MAX_RANGE_MBR`
  and has never independently rejected a formation -- confirmed live, `desk_playbook_detect.py:439`
  already implements both gates verbatim (`jump < jump_min_mult*base_range or jump <
  jump_min_move_mbr*mbr`).
- §3.6: rename the left-rim "near session-high-so-far" constant from `PLAYBOOK_RIM_MATCH_MBR` to
  `PLAYBOOK_NEAR_EXTREME_MBR` -- confirmed live, `desk_playbook_detect.py:677,680` already read
  `params["near_extreme_mbr"]` there; the rim-to-rim test at line 674 correctly keeps
  `rim_match_mbr` and is untouched.
- §3.7 Trigger clause: narrow to name the arming-completing touch `b` specifically -- confirmed
  live, `_range_trade_side` (`desk_playbook_detect.py:1068-1153`) already anchors only on
  `b = armed_touches[-1]`.
- Every one of the four above is a **prose-only** edit verified against the code that already
  ships -- never "fix" code to match old prose. `git diff` on each detector function named must
  show zero changed lines (TC-1..TC-4). Re-locate by symbol/grep, not by these line numbers alone
  -- they are confirmed accurate as of this writing, not a promise the file hasn't moved.
- R-3.1 (the `range_trade` degenerate-trigger-reference clause, spec §3.7 Edge cases) needs
  **zero action** -- already ratified and shipped verbatim. Do not touch it.

**B. The one new disclosure, spec-first (R-3.2(b)):**
- `docs/playbook-detector-spec.md` §3.7 Disclosures clause splits into two named fields, written
  BEFORE any code: `crossed_midrange` renamed exactly to "did price cross the range midpoint on
  the approach" (its actual shipped semantics, `desk_playbook_detect.py:1180-1190`); a NEW field
  disclosing whether the prior swing turned at the range's midpoint (the book's own midrange
  rule), with its own mechanical bar-by-bar definition. Field name is pre-committed by the
  decomposer (`runs/goal-session-playbook/state/assumptions.md`, iter-10 entry):
  `geometry.turned_at_midrange: boolean`.
- Binding constraints (non-negotiable, per R-3.2(b)): reuse ONE already pre-registered constant --
  either `PLAYBOOK_RANGE_HOLD_TOL_MBR` (this detector's own "held" tolerance) or the
  `swing_pivots` primitive keyed by `PLAYBOOK_PIVOT_LOOKBACK_BARS` -- never mint a new one;
  disclosure-only (never gates/suppresses/creates a signal); lookahead-clean (reads only bars
  at-or-before the arming-completing touch `b`, same discipline `crossed_midrange` already uses);
  computed for both long and short sides; optional key in the payload and in `types.ts`.
- **Escape hatch (a legitimate outcome, not a failure):** if the definition genuinely cannot be
  expressed without a new constant, DROP it, add nothing to the constants table, and record the
  drop + reason in `runs/goal-session-playbook/state/assumptions.md` and `iteration-state.md`. If
  dropped, skip the `types.ts`/`page.tsx` edits below -- J-06's acceptance is unaffected either way.
- Implement in `_range_trade_side` (`desk_playbook_detect.py:1068`, geometry dict ~1241-1248): add
  `geometry.turned_at_midrange` beside the existing `crossed_midrange`.
- Prove `playbook_input_signature`/`playbook_parameters()` are byte-unchanged by this iteration's
  own code (no constant value changed) -- extend
  `test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_version`
  (`test_desk_playbook.py:300`) with BOTH directions: monkeypatching the reused constant still
  moves params+signature; leaving every constant untouched reproduces the byte-identical
  pre-iteration signature on the same bar/member inputs.

**C. Two carried test/fixture defects, zero product-code diff:**
- `runs/goal-session-playbook/journey-scripts/J-10.json` step 6: replace the fixture-rebuild
  hash `9597251432bd9e75` with a static, always-rendered `/desk` shipped-section string.
  `iteration-state.md` names the pre-corruption value as `"Forward Returns"` -- the likely correct
  fix; confirm it renders unconditionally (not data-dependent) before locking it in.
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py`: `_copy_kept_symbol_series` (line 201,
  called from `main()` at line 283) copies AAPL's real bar files with `shutil.copy2` but never
  updates the scoped rig's `bar_index.db`, so `GET /research/bars?symbol=AAPL` (what
  `/structure`'s chart fetches) resolves through `BarIndex.list()` and sees nothing -- a different
  cache path (levels/tradability) already shows real numbers, which is why this was missed before.
  Fix: call the existing `desk_index_reconcile.run_reconcile(bar_store, bar_index)`
  (`app/research/desk_index_reconcile.py:150`, the sole `BarIndex.reindex()` repair path) right
  after the copy step. Add a smoke check proving the scoped `bar_index.db` gains AAPL entries.

## Agents Required
- backend-data: yes -- spec-doc edits (A+B), `_range_trade_side`'s new field, the signature
  counter-test, range_trade fixture extensions, the seed-script index-repair fix + smoke check
- frontend-ux: yes -- `types.ts` optional field + one conditional chip in `page.tsx`'s existing
  range_trade geometry line (skip both if B is dropped-and-surfaced)

Frontend Present: yes

## Files to Create/Modify
- `docs/playbook-detector-spec.md` -- §3.3, §3.6, §3.7 (Trigger + Disclosures), §3.8 Caps line,
  §1 constants table row -- per R-3.2(a)/(b)/(c)/(d)/(e); zero code diff proven for (a)/(c)/(d)/(e)
- `apps/backend/app/research/desk_playbook_detect.py` -- `_range_trade_side` (~1068-1266): add
  `geometry.turned_at_midrange` (or drop-and-surface, no diff here)
- `apps/backend/tests/test_desk_playbook_detect.py` -- range_trade fixture(s): a True/False
  `turned_at_midrange` pair (near-miss required), a pre-iteration-style record with the key absent
- `apps/backend/tests/test_desk_playbook.py` -- extend the line-300 counter-test, both directions
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py` -- index the copied AAPL series via
  `desk_index_reconcile.run_reconcile`
- `apps/backend/tests/test_desk_index_reconcile.py` (or a small new test near the seed script) --
  the smoke check that indexing actually happened
- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` (~1523): add
  `turned_at_midrange?: boolean` beside `crossed_midrange?: boolean`
- `apps/frontend/app/desk/page.tsx` -- (~5104): one new conditional chip beside the
  `crossed_midrange` chip in the `range_trade` geometry `<p>`
- `runs/goal-session-playbook/journey-scripts/J-10.json` -- step 6 expect text
- `docs/handoffs/goal-playbook-iter-10-dev.md` -- required
- `docs/handoffs/goal-playbook-iter-10-frontend.md` -- if the field ships (matches iter-4/5/7/8/9
  precedent of a separate frontend handoff whenever `page.tsx`/`types.ts` change)

Do NOT touch: `desk_forward.py` (zero-diff era invariant), `desk_playbook_evidence.py` (the new
field is a Signals disclosure only, never pooled), `app/mcp/__init__.py` (existing `desk_playbook`
proxy forwards the field automatically), any `Config` field, `docs/goal.md` (owner-authored).

## UI Evolution
- New user-facing capability: an already-shipped `range_trade` signal's geometry line can now also
  disclose whether the approach swing turned at the range's midpoint (the book's own midrange
  rule), alongside the existing "crossed midrange" disclosure -- informational only, never advice.
- New information displayed: `turned_at_midrange: boolean` as one more inline chip, shown only
  when true, matching how `crossed_midrange`/`absorption_bar_present` already render.
- New user actions: none -- no new buttons, forms, or controls.
- UI surface changes: one new conditional `<p>` chip inside the EXISTING
  `desk-playbook-signal-range-trade-geometry` element. No new section, no new page.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the exact existing chip idiom
  (`{condition && " · label text"}` inside the shipped `<p className="mt-1 text-[11px]
  text-slate-500">`) -- no new component, no new Tailwind class.
- Layout: unchanged -- the chip lands inside the already-shipped Playbook Signals row; every other
  kept `/`, `/structure`, `/desk` surface renders exactly as shipped (J-10 re-verifies this).
- Key visual effects: none new.
- States to handle: field absent on pre-iteration records renders nothing (same as any other
  optional geometry field); `false` renders nothing (same convention as `crossed_midrange`);
  `true` renders the chip. `/structure`'s chart must show real candles, not the blank-canvas state,
  once the seed-script fix lands.

## Key Test Scenarios
- TC-1..TC-4: `git diff` on every detector function touched by the four doc-only spec edits shows
  zero changed lines.
- TC-5: §3.7 Disclosures clause is split spec-first, citing only an already-pre-registered
  constant -- no new constants-table row.
- TC-6/TC-7: a `turned_at_midrange` True fixture and a matching False near-miss; every
  pre-existing range_trade field (`trigger_price`, `invalidation_price`, `crossed_midrange`,
  `absorption_bar_present`, `range_width_mbr`, ...) byte-unchanged from its pre-iteration value.
- TC-8: a pre-iteration record (e.g. one of the 87 real signals under signature
  `16a2734d10c91ea7`) serves via `GET /research/desk/playbook` with the key absent (never null),
  HTTP 200.
- TC-9: monkeypatching the reused constant moves `playbook_parameters()`/the signature; leaving
  every constant untouched reproduces the byte-identical pre-iteration signature on the same
  inputs; `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- TC-10 (contingent): if dropped, the reason is recorded in `assumptions.md` + `iteration-state.md`
  and nothing is added to the constants table.
- TC-11: the new chip renders on `/desk` for a `turned_at_midrange: true` signal;
  `tests/test_copy_discipline.py` passes over the new copy unmodified (no lint-file edit needed --
  it already globs `app/**/*.tsx`).
- TC-12: fixed `J-10.json` step 6 asserts a static shipped string (never a hash / a value the run
  itself just produced) and passes deterministic replay.
- TC-13: post-fix, `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z` + Load renders real candles
  on the scoped rig (fresh screenshot); the resistance/support numbers (e.g. `300.11-302.2`) stay
  byte-identical; no bar file content mutated.
- TC-14: full backend suite exits 0, >=2163 passed, 8 skipped, no regressions.
- TC-15/TC-16: store-scope guard reports zero delta against the operator's real store (automatic
  since iter-9 -- no manual script invocation needed); coherence-auditor confirms
  `turned_at_midrange` rides the ALREADY-registered "Playbook records" row (same owner/endpoint,
  `desk_playbook_detect.py` + `desk_playbook.py` / `GET /research/desk/playbook`), zero
  `app/mcp/__init__.py` diff.
- Required-still-passing J-01/J-02/J-03/J-04/J-05/J-07/J-08/J-09 green via deterministic replay
  (LLM fallback on any miss); J-06 and J-10 verified via browser-qa-agent with fresh screenshots.
  Any browser evidence captured before BOTH fixes (B's code + C's seed-script fix) land is voided
  and must be re-captured on a fresh rebuild -- never mix pre-fix and post-fix screenshots.
