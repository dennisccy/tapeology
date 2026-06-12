# goal-i_will_be_super_rich_with_my_loved_ones-iter-20 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-20
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

The **holding-period management stance** (J-53; data-contract row 25 stance half) — the first
decision-support cue, on the evidence layer that now backs it. While the user HOLDS a journaled
position (an entry-marked, unresolved thesis), the thesis strip on `/` answers *"does the tape still
support this position?"* with `thesis_intact | thesis_weakening | thesis_invalidated` + evidence, plus
live distance-to-invalidation ($ and R) and open R in mono. A pure derivation from the row-16 published
verdict — no new indicator, no persistence (schema stays v7), read-only over the engine.

### Backend
- **New module `apps/backend/app/research/stance.py`** — the single-owner stance evaluator:
  - `StanceEvaluator` — holds one entry-marked thesis's PUBLISHED stance, advanced per event from the
    monitor's current published verdict. Maps verdict → stance, publishes through its OWN config-owned
    logical-time dwell (`management_stance_dwell_seconds`, no per-tick flap), EXCEPT `thesis_invalidated`
    which is dwell-exempt + terminal (mirrors the hard invalidation trigger).
  - `compute_position_readouts(...)` — the live readouts (`distance_to_invalidation` in $ and R,
    `open_r`) computed via the ONE `marks.r_basis()` helper — the stance is its **fifth registered
    consumer** (row 27), never a second formula. `open_r` is signed by direction with the SAME
    convention as `marks.py`'s realized move (favorable move = positive). A degenerate R==0 yields
    `None` for the R-unit figures (never inf/NaN), the dollar distance still reads.
- **`monitor.py`** — wired the stance into the observer lifecycle:
  - `build_projection(...)` gained `management_stance` / `management_stance_evidence` params; it serves
    the additive `management_stance` (`{value, evidence, label}`), `distance_to_invalidation`
    (`{dollars, r}`), and `open_r` keys ONLY when a stance is supplied AND an entry mark exists.
  - `ResearchMonitor` creates a fresh `StanceEvaluator` in `set_thesis` + the J-47 adopt path, clears it
    in `clear_thesis`, advances it in `on_event` AFTER the verdict step (reading the just-published
    verdict; the invalidated verdict carries the offending-print evidence onto the terminal stance), and
    reads its published stance into `projection()`. A failed monitor read serves NO stance.
  - The unwatched-survivor + mismatched-source (`not_evaluated`) paths pass NO stance → keys ABSENT
    (no frozen-stale stance; the "no entry mark yet" vs "not currently evaluated" absences are distinct).
- **`taxonomy.py`** — the management-stance display copy (row 24), served additively by
  `GET /research/taxonomy`: `MANAGEMENT_STANCES` (three labels), the `_VERDICT_TO_STANCE` map +
  `stance_for_verdict()` (the full five-verdict mapping; pending → `thesis_weakening`, never intact),
  `STANCE_PENDING_EVIDENCE` (the honest J-54 entry-while-pending copy), the two DISTINCT absence copies
  (`STANCE_ABSENCE_NO_ENTRY_MARK` / `STANCE_ABSENCE_NOT_EVALUATED`, iter-15 lesson), and the
  journaled-measurement readout caption. All present-tense, factual, never imperative/predictive.
- **`config.py`** — new `management_stance_dwell_seconds: float = 3.0` (documented research default),
  EXCLUDED from `config_fingerprint` (the stance is never persisted → serving-only, iter-12/16 pattern;
  documented rationale + a fingerprint-stability test + the real-threshold counter-test).

### Frontend
- **`lib/types.ts`** — `ManagementStance`, `DistanceToInvalidation`, the three optional projection keys
  (`management_stance`, `distance_to_invalidation`, `open_r`), and the taxonomy stance fields.
- **`components/ThesisStrip.tsx`** — a new `ManagementStanceBlock` (+ `StanceReadout`) rendered inside
  `ActiveThesis`. Shows the stance chip in the established palette (`thesis_intact` emerald,
  `thesis_weakening` amber, `thesis_invalidated` rose with the terminal ringed treatment — the label
  TEXT is taxonomy-owned, read verbatim), the evidence line, and the distance ($ and R) + open R in
  `font-mono`. Renders ONLY when the backend serves the stance keys — zero client-side arithmetic, zero
  client-side stance derivation. Without the keys the strip is pixel-identical to today (J-38/J-42/J-50).

## Files Changed
- `apps/backend/app/research/stance.py` -- NEW: stance evaluator (dwell) + position readouts (r_basis consumer #5)
- `apps/backend/app/research/monitor.py` -- wire StanceEvaluator into the observer lifecycle + build_projection additive keys
- `apps/backend/app/research/taxonomy.py` -- management-stance enum + verdict→stance map + pending/absence/caption copy; served via /taxonomy
- `apps/backend/app/config.py` -- `management_stance_dwell_seconds` (serving-only, fingerprint-excluded)
- `apps/backend/tests/test_research_stance.py` -- NEW: stance map, dwell, invalidated-exempt, four-quadrant readout sign proof, fingerprint stability + counter
- `apps/backend/tests/test_research_monitor.py` -- stance presence rules (no entry mark / entry-marked confirming / pending / invalidated / not-evaluated / failed) end-to-end on SIM-SHIFT
- `apps/backend/tests/test_research_api.py` -- /taxonomy management-stance canary + copy-lint; REST==WS stance keys with an entry mark
- `apps/frontend/lib/types.ts` -- ManagementStance / DistanceToInvalidation / projection + taxonomy stance keys
- `apps/frontend/components/ThesisStrip.tsx` -- ManagementStanceBlock in the holding-period view (renders verbatim)

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **696 passed, 1 skipped, exit 0** (the 1 skip is the credentialed live-data test). +25 new tests
this iteration (16 in `test_research_stance.py`, 9 stance presence-rule tests in the monitor suite, plus
the taxonomy-canary + REST==WS stance tests in the API suite).

Key proofs:
- Stance mapping for ALL five published verdicts incl. the honest `pending` case (never `thesis_intact`).
- Dwell: a verdict flip publishes the stance only after the configured dwell (no per-tick flap);
  `thesis_invalidated` dwell-exempt + terminal.
- Distance + open R via `marks.r_basis()` (registered-consumer) with **four-quadrant sign proof**
  (long+short × favorable+adverse last), exact values asserted; degenerate R==0 → None R-units.
- Presence rules: keys absent without an entry mark; absent on the surviving not-evaluated path (no
  frozen stance); terminal `thesis_invalidated` present at the auto-resolve; absent when monitor failed.
- REST `/thesis/active` == WS `thesis` key carry the stance keys (one projection, J-08).
- Observer-equivalence suite still green (the stance never mutates the engine — byte-identical).
- Config fingerprint: stance dwell excluded (stability test) + a real threshold still moves it (counter).
- Copy-lint over the new taxonomy strings: no imperative trade words (buy/sell/enter/exit/should).

Frontend: `cd apps/frontend && npx tsc --noEmit` → **exit 0** (type-check only; `npm run build` deliberately
NOT run — the shared dev-server `.next` is untouched per the iter-2/18 lesson; build is for browser-qa).

## Pre-handoff verification
- **Service startup / canary:** started uvicorn on an isolated port (`:8792`, `TAPEOLOGY_JOURNAL_DB=:memory:`),
  confirmed `/health` → 200 and `GET /research/taxonomy` carries the NEW management-stance copy
  (`management_stances`, `stance_absence` with two distinct keys, `stance_readout_caption`) — the
  iter-20 code-identity canary. Process killed afterward; no stray `uvicorn main:app` processes remain
  (verified 0). The pre-existing harness `next dev` processes were left untouched (shared `.next`).

## Known Issues
- None functional. The stance's own dwell layers on the verdict's already-published (dwell-gated) verdict,
  so on SIM-SHIFT a `thesis_intact` capture needs the confirming tape to persist a few seconds past the
  entry mark before the stance settles (browser QA should budget for both dwells — iter-1 lesson). The
  weakening→invalidated end-states are in the append-only timeline if a transient frame is missed
  (iter-1 fallback); `thesis_intact` and `thesis_invalidated` end-states are in pixels.
- Out of scope (deferred to J-63/J-64 per the spec): the entry checklist, live named-check margins,
  `no_fresh_tape` freshness, `delivery_lag_seconds`. No engine/store/schema/endpoint/route change made
  (schema stays v7; `verdict_events` untouched; no new endpoint; no nav/blueprint-skeleton change).
