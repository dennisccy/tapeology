# Iteration 10 — Coherence Audit

**Iteration:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration extends the existing **row-6 `stream_status`** with two new engine-owned lifecycle
values (`waiting`, `failed`). The blueprint's iter-10 header note explicitly registers this as an
additive extension with no new endpoint and no new producer. The checks below cover all contract
rows touched or potentially duplicated by the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 6: `stream_status` (waiting) — new rung | OK | `apps/backend/app/engine/tape_engine.py:161` — single flip `connecting/waiting → live` in `process_event`; `apps/backend/app/watch_manager.py:177,208,281` — feeders set `waiting` (sole writers); served verbatim by serializers at `apps/backend/app/serializers.py:59,88,137`; UI reads at `apps/frontend/app/page.tsx:145` and `apps/frontend/components/Cockpit.tsx:18` |
| Row 6: `stream_status` (failed) — new rung | OK | `apps/backend/app/watch_manager.py:192,229,335` — `_feed`, `_feed_paced`, `_feed_live` each flip to `failed` on non-CancelledError exception (sole writers); served verbatim; UI reads at `apps/frontend/app/page.tsx:146` |
| Row 6: single-producer rule | OK | No second `stream_status` writer introduced. All `set_stream_status(...)` calls remain in `watch_manager.py` feeders and `tape_engine.py:set_stream_status`/`process_event`. Serializers pass through verbatim. UI reads `snapshot.stream_status` verbatim with no client-side recomputation. |
| Row 1–5, 7–12: all other registered values | OK | Diff touches no classification logic, no feature computation, no OHLC history binning, no symbol-search adapter, no market-clock module, no historical-window datetime resolver, no paused-flag logic. Engine math is an empty diff aside from the additive `waiting` rung in `process_event` (a status label change, not classification). |
| WaitingState display text | OK | `apps/frontend/components/IdleState.tsx:49–82` — `WaitingState` component reads `symbol` and `mode` from page state (existing props); it does NOT recompute any rows 1–6 engine value. The mode label is a display-only `MODE_LABEL` map. |
| `pauseable` check in TopBar | OK | `apps/frontend/components/TopBar.tsx:172` — the `["connecting","live","stale"].includes(snapshot.stream_status)` check gates the Pause button visibility; it does not compute a new displayed value and `waiting`/`failed` not being in the set is correct (there is nothing to pause on a waiting/failed stream). Not a duplicate computation of any contract value. |

## Information Architecture check

The blueprint IA for this iteration: all J-25/J-26/J-27 journeys live on the single `/` HOME
cockpit area, ≤1 click after Watch. The diff introduces no new page, no new route, and no nav
change.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `WaitingState` in-place cockpit treatment (`/`) | OK | `apps/frontend/app/page.tsx:187–194` routes `snapshotWaiting` to `<WaitingState>` in the main cockpit area of the single `/` route. No new route. No nav change. |
| Snapshot-borne `StreamFailedState` (`/`) | OK | `apps/frontend/app/page.tsx:183–187` routes `snapshotFailed` to `<StreamFailedState>` in the same cockpit area. Reuses the existing component (no new page). |
| `TopBar.tsx` status dot: `waiting` + `failed` entries | OK | `apps/frontend/components/TopBar.tsx:38–47` — new entries in the existing `STREAM_DOT` map. No new nav element, no new section. |
| `snapshotConnecting` transient guard (`/`) | OK | `apps/frontend/app/page.tsx:151,194–197` — in-place treatment, same cockpit area. No new route. |
| No new routes anywhere | OK | `apps/frontend/app/` contains only `globals.css`, `layout.tsx`, `page.tsx` (unchanged set). `find` confirms no new page directories. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The `pauseable` check at `apps/frontend/components/TopBar.tsx:172` does not include `waiting` or
  `failed` in its set, which means Pause is hidden while the stream is in those states. This is
  semantically correct (there is nothing useful to pause on a stream with no data or one that has
  already failed), but it is worth noting as an intentional design decision in case a future
  iteration adds auto-retry that would re-open the pause affordance in `waiting`.

- The `WaitingState` component at `apps/frontend/components/Cockpit.tsx:18–21` serves as a
  backstop guard independent of the primary routing in `page.tsx`. This is belt-and-suspenders and
  does not create a second producer — both paths read the same `snapshot.stream_status` field
  verbatim. Redundant presentation guards are not a coherence violation; they are advisory as they
  could diverge if the waiting message text needs updating (two display sites for the waiting
  treatment: `IdleState.tsx` component used by both, so in practice it is one definition).
