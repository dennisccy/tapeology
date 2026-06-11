# goal-i_will_be_super_rich_with_my_loved_ones-iter-9 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-9
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-47 — a thesis carrying a real entry mark survives an interrupted watch instead of being orphaned;
plus the iter-8 carry: the mandatory favorable-dominant `directional_impact` dominance pins.

- **Expiry reason now distinguishes user stop from stream exhaustion.** The engine status string
  alone could not tell a USER stop apart from a stream that ran out (both flip `stream_status` to
  `closed`). The `TapeEngine.set_stream_status` now accepts an optional `end_reason` (stored, read
  via the new `TapeEngine.end_reason` property; the `on_status(status)` observer signature is
  UNCHANGED). `WatchManager.stop()` stamps `watch_stopped` before cancelling the feeder; every
  feeder's natural-exhaustion path stamps `stream_closed`. The monitor reads `engine.end_reason` to
  record the right reason. J-50's verified `expired(stream_closed)` leg is preserved (and is the
  default when no engine reason is available).
- **Entry-marked theses survive stop / failure / restart as active-but-not-evaluated.**
  `ResearchMonitor.on_status('closed'|'failed')` now checks `store.has_entry_mark`: an entry-marked
  active thesis is NOT expired — it stays `active` in the store, NO verdict event is appended while
  unwatched, and the monitor detaches. An unmarked thesis still auto-expires with the explicit
  reason (`watch_stopped` / `stream_closed` / `failed`).
- **Surviving thesis served by the SAME projection path.** A single module-level
  `monitor.build_projection(...)` is the ONE projection builder (data-contract row 15). Both the
  live monitor and the registry's unwatched-survivor fallback (`ResearchRegistry._surviving_projection`)
  call it — never a second computation. `GET /research/thesis/active?ticker=` for a stopped ticker
  with a surviving entry-marked thesis returns it with `monitor_status: "not_evaluated"` and the
  backend-owned notice (`monitor_notice`). `thesis: null` remains the answer when nothing survives.
- **Re-attach on the matching source.** On re-watch, `ResearchRegistry.on_engine_created` offers a
  surviving entry-marked active thesis to the fresh monitor (`monitor.offer_surviving`). The monitor
  adopts it only once the FIRST snapshot confirms `snapshot.scenario == thesis.bound_source`
  (`_maybe_adopt_surviving`), appends exactly ONE `watch_restarted` gap event (append-only, no
  backfill), and resumes evaluation from a fresh evaluator (post-restart evidence only). Idempotent:
  a second snapshot does not append a second gap event.
- **Mismatched source is never adopted/evaluated.** If the first snapshot's source differs from
  `bound_source`, the thesis is never adopted, no verdict is appended, and the projection carries the
  explicit backend-owned mismatched-source notice naming the declared source.
- **Startup sweep exempts entry-marked actives.** `store.expire_stale_actives` skips an entry-marked
  active thesis (no expiry event appended for it) and still expires unmarked stale actives with the
  explicit interruption reason. This is also J-51's "entry-marked survives restart" leg, pre-built
  here (J-51 itself stays untargeted until `/journal` exists).
- **Backend-owned lifecycle copy** (taxonomy, data-contract row 24): `not_evaluated_notice(...)`
  and `mismatched_source_notice(...)`, plus a `MONITOR_STATUSES` enum exposed in
  `GET /research/taxonomy`. All present-tense, descriptive, thesis-attributed.
- **Mandatory favorable-dominant dominance pins (iter-8 carry):** unit-pinned in both directions with
  the EXACT named parameters — long `buy_price_impact=+0.40`, `sell_price_impact=-0.14` → `met`;
  short `sell_price_impact=-0.40`, `buy_price_impact=+0.14` → `met`. No production-code change was
  needed; the pins assert the existing dominance semantics.

No schema change (gap events are appended `verdict_events` rows; entry-mark presence is already
queryable). No engine/classifier/feature/provider behavior change (the engine `end_reason` is
additive display/lifecycle metadata, never read by classification — determinism + observer
equivalence preserved).

## Files Changed
- `apps/backend/app/engine/tape_engine.py` -- optional `end_reason` on `set_stream_status` + `end_reason` property (additive lifecycle metadata; observer signature unchanged).
- `apps/backend/app/watch_manager.py` -- `stop()` stamps `watch_stopped`; feeders stamp `stream_closed` on natural exhaustion.
- `apps/backend/app/research/monitor.py` -- shared `build_projection`; entry-marked survival (`_detach_not_evaluated`); reason-aware expiry (`_terminal_reason`); re-attach (`offer_surviving` / `_maybe_adopt_surviving` with one `watch_restarted` gap, idempotent); mismatch notice; engine handle (`attach_engine`).
- `apps/backend/app/research/routes.py` -- registry attaches engine to monitor + offers surviving thesis on re-watch; `projection_for` falls back to `_surviving_projection` (same builder, `not_evaluated` + notice).
- `apps/backend/app/research/store.py` -- `expire_stale_actives` exempts entry-marked actives.
- `apps/backend/app/research/taxonomy.py` -- backend-owned not-evaluated / mismatched-source copy + `MONITOR_STATUSES` enum.
- `apps/backend/tests/test_research_monitor.py` -- favorable-dominant pins; expiry-reason tests; entry-marked survival; re-attach + idempotence; cross-source mismatch (REQUIRED unit leg).
- `apps/backend/tests/test_research_store.py` -- startup-sweep entry-marked exemption.
- `apps/backend/tests/test_research_lifecycle.py` -- NEW end-to-end J-47 (UT-A survive stop served not_evaluated; UT-B re-attach + one gap event; UT-C unmarked expires watch_stopped; abandoned-refused-while-not-evaluated).
- `apps/frontend/lib/types.ts` -- `monitor_status: "not_evaluated"` + `monitor_notice` on `ThesisProjection`.
- `apps/frontend/lib/api.ts` -- `fetchActiveThesis(ticker)` REST helper (used only off-stream, after Stop).
- `apps/frontend/components/ThesisStrip.tsx` -- `NotEvaluatedThesis` variant (notice verbatim, no live verdict/controls).
- `apps/frontend/app/page.tsx` -- after Stop, fetch surviving thesis and keep it on the cockpit surface as not-evaluated; cleared on a new watch.

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **427 passed, 1 skipped** (the skip is the credentialed live-integration test). Includes the
observer-equivalence suite, J-50 expiry tests, J-52 marks, and J-42/J-41 verdict semantics — all green.

Frontend: `cd apps/frontend && NEXT_DIST_DIR=.next-iter9-verify npx next build` → compiled + type-checked
successfully (verify dist dir removed afterward; never built against the shared `.next` / `.next-qa`).

## Live Verification (not mocked)
Booted the real backend (`uvicorn main:app`) on an isolated port and exercised the live REST flow:
watch `SIM-BUYER` → declare trend_continuation/long → mark entry → `DELETE /watch` → `GET
/research/thesis/active` returned `monitor_status: not_evaluated` with notice
`"not currently evaluated — re-watch this source to resume (buyer_control)"`; re-watching the same
source returned `monitor_status: ok` again. Backend boots cleanly and restarts on the same port with
no conflict; all spawned servers were killed (no lingering uvicorn).

## Known Issues
- Browser QA (the UT-J-47-A/B/C pixel captures + non-regression re-checks) runs in the qa step, not
  in dev. The dev-side proof is the unit/integration suite + the live REST smoke above.
- The cross-source mismatch leg is unit-proven (per goal.md): the sim REST/browser environment cannot
  produce a mismatched source for the same ticker (a sim ticker is bound to its scenario), so the
  mismatch path is covered by `test_reattach_mismatched_source_not_adopted_no_verdict_with_notice` and
  the monitor's mismatch projection branch — not faked browser-side.
- J-51 benefit is incidental (sweep exemption + reason honesty) and is NOT claimed — it stays failing
  until the `/journal` page journeys land (J-55+).
