# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — UX Regression Review

**Date:** 2026-06-16

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

This iteration added no new capabilities. The plan explicitly states "New user-facing capability: None" and confirms all surfaces exercised this iteration already existed. The iteration is a verification-only pass; the application source is byte-for-byte identical to the previous iteration (J-68 byte-identity holds: both `git status --porcelain apps/` and `git diff --stat HEAD -- apps/backend/ apps/frontend/` return empty, confirmed live).

No discoverability assessment is required for new capabilities.

---

## Regression Risk

The current phase's ui-surface-map reports zero changed components (0 modified frontend source files, 0 modified backend source files). No shared component was touched, so no new regression was introduced by this iteration's changes.

However, UT-08 from the browser QA results reveals a pre-existing gap that this iteration's required spot-checks were meant to confirm as still-passing:

**UT-08 — Unknown symbol in Live mode shows no explicit failure message (FAIL)**

The iter-29 plan lists J-14 ("unknown symbol → not a tradable symbol") as a required-still-passing spot-check. The browser QA agent entered `ZZZNOEXIST` in Live mode and found:
- The cockpit silently connected and showed `stale` status with an empty quote panel (all dashes)
- No explicit error message, no "not a tradable symbol" text, no error panel
- The cockpit treated the bogus ticker as a valid IEX watch that had no data

The journey-history.json records J-14 as `passing` last verified in iter-28, but that verification note reads: "unknown symbol via REST → 'not a tradable symbol' 404". This is a REST API assertion, not a Live-mode browser UI assertion. The `SymbolNotTradable` exception and 404 path is documented in the Historical mode code path (`fetch_historical('ZZZZNOTREAL', ...)` raised `SymbolNotTradable` per iter-27 dev handoff). Live mode appears to accept any symbol string, open a socket, and silently serve empty data without the pre-flight symbol validation that blocks invalid symbols in the Historical path.

This is not a regression introduced by iter-29 (which made no code changes). It is a pre-existing gap: J-14's "unknown-symbol honest panel" was demonstrated via REST and Historical mode, but not via the Live mode UI path, and iter-29 surfaced that this mode-specific gap persists.

Shared component risk: zero (no components were touched this iteration).

---

## UI vs Backend Parity

This iteration verified existing backend capabilities, not new ones. The backend delivers:
- `stream_status` transitions (`live → stale → live`) via `GET /tape/{t}/summary` — confirmed working, surfaced correctly in the cockpit status indicator
- `data_feed: "iex"` stamp in the snapshot — confirmed working, surfaced correctly via `FeedBasisBadge`
- IEX-vs-SIP disclosure text from `GET /research/taxonomy` — confirmed working, rendered inline in the cockpit viewport
- `data_feed = iex` on journal rows produced during a live IEX watch — confirmed working, visible in the `/journal` table FEED column

All three verified backend capabilities are correctly surfaced in the UI. No backend capability is hidden or absent from the UI.

One gap between the plan's stated expectation and the observed UI behavior: the plan states J-14 ("unknown symbol → not a tradable symbol") must remain passing as a spot-check. The browser QA found this does not hold in Live mode. The backend does handle unknown symbols via `SymbolNotTradable` (mapped to a 404 with "not a tradable symbol" in the API), but the Live-mode frontend path does not surface this rejection to the user — it silently presents an empty `stale` watch.

---

## Flags

### Hidden Capabilities

None. All capabilities verified this iteration were already reachable from the home page: the cockpit live status indicator is on-screen during any active watch (0 extra clicks from `/`), the `FeedBasisBadge` is visible in the cockpit status area, and the `/journal` table is linked from primary navigation.

### Undiscoverable Capabilities

None. No new navigation paths or capabilities were introduced.

### Potential Regressions

**J-14 (unknown-symbol honest panel) — Live mode path does not surface an explicit error message**

- Prior feature: J-14b, established that entering an unknown symbol should produce an honest "not a tradable symbol" rejection rather than a silent empty cockpit
- Shared element: Live mode watch initiation (`POST /watch/{ticker}` + cockpit rendering)
- Current iteration: no code was changed, but browser QA explicitly failed UT-08 — entering an invalid symbol in Live mode shows `stale` status with empty quote data and no user-facing error message
- Risk level: medium — this is a pre-existing gap surfaced by this iteration's spot-check, not a new regression, but it was listed as a required-still-passing scenario in the iter-29 plan and the browser QA verdict is FAIL
- Note: the doubled symbol name (`ZZZNOEXISTZZZNOEXIST`) in the UT-08 actual result suggests a browser input-field artifact (the previous typed value was not cleared before typing), but even with this artifact the core finding holds — no explicit error message was surfaced

### Visual Consistency

No new pages, panels, components, or style tokens were introduced. The existing cockpit surfaces exercised this iteration (live status indicator, `FeedBasisBadge`, `/journal` table) were built in prior iterations and carry their established DESIGN SYSTEM conformance (emerald/green for `live`, amber for `stale`, mono numerics, dark instrument-panel palette). No new arbitrary values or off-token styles were introduced.

---

## Recommendation

**No action required from this reviewer** — this is a verification pass and no source changes occurred.

However, the UT-08 failure warrants a follow-up evaluation decision: the iter-29 plan lists J-14 as a required-still-passing spot-check that did not pass in Live mode browser testing. The goal-evaluator should assess whether J-14's "unknown symbol" leg should be re-scoped to explicitly cover the Live-mode UI path (not just the REST/Historical path that has been demonstrated previously), or whether the existing REST-grounded evidence is sufficient for the journey's acceptance criteria. If the Live-mode UI path is in scope for J-14, a targeted fix is needed: the cockpit should surface the backend's existing "not a tradable symbol" 404 response as an explicit user-facing message rather than silently rendering an empty stale watch.
