**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-8 (goal-i_will_be_super_rich-iter-8)

**Session:** i_will_be_super_rich  
**Iteration index:** 8  
**Iteration name:** goal-i_will_be_super_rich-iter-8  
**Snapshot SHA:** 0cffbbfc0e45c4f36482fa5fab0eb41486ab51db  
**Audited files changed:**  
- `apps/frontend/components/TopBar.tsx`  
- `apps/frontend/lib/datetime.ts`  
- `runs/goal-session-i_will_be_super_rich/state/blueprint.md` (additive clarification of row 12 only)  
- `apps/backend/tests/test_window_resolution.py` (new, untracked — test-only, no behavioral change)

---

## Step 1 — Data Contract

### Row 12: Resolved historical window

**Registered canonical computing module:** `apps/frontend/lib/datetime.ts` — the resolution function resolves the user's local selection and ET session anchors to tz-aware UTC instants once, before the POST body is built.

**Registered canonical serving endpoint:** `POST /watch/{ticker}` body `{mode:"historical",start,end,speed}` (timezone-aware instants).

**Check — duplicate computation:** The diff adds `resolveLocalWindowInstant`, `resolveSessionPreset`, `etWallTimeToUtc`, `localZoneLabel`, and `zoneOffsetMinutes` exclusively to `apps/frontend/lib/datetime.ts`. The only consumer is `TopBar.tsx`, which imports all resolution functions from that single module. No second module computes the window resolution; no other frontend component independently resolves local time to UTC. No violation.

**Check — non-canonical source:** `TopBar.tsx:163–166` builds the POST body start/end exclusively via `presetWindow` (verbatim resolved UTC instant from `etWallTimeToUtc`) or `resolveLocalWindowInstant` (from `apps/frontend/lib/datetime.ts`). This replaces the prior naive `${date}T${startTime}` construction — the canonical module is now the sole resolver, not a second one. No violation.

**Check — backend test:** `apps/backend/tests/test_window_resolution.py` calls `_parse_window_dt` from `app.main` directly (source-of-truth verification, not a new computation owner). It does not introduce a second window-resolution path; it tests the existing canonical backend parser's behavior on offset-bearing values. No violation.

**New values check:** The new displayed values are:
1. The **local timezone label** (e.g. `Asia/Hong_Kong`) shown beside the Historical date/time inputs — this is a display-only value derived from `Intl.DateTimeFormat().resolvedOptions().timeZone`. It is a browser-runtime label, not a backend data value. It is subsumed by and consistent with the row-12 "explicit local zone label" description already registered in the blueprint's row 12.
2. The **quick-pick local-equivalent annotations** (e.g. `09:30 PM local`) shown on the US-session buttons — these are derived from the same `lib/datetime.ts` owner via `localTimeAnnotation`/`resolveSessionPreset`. Subsumed by row 12's "US-session quick-picks … annotated with its local equivalent."

Both new display values are display derivatives of the row-12 canonical owner and do not constitute new independently-computed concepts. No unregistered-value WARN needed.

**Step 1 result: No violations.**

---

## Step 2 — Information Architecture

**New routes/pages:** None. The UI surface map and the diff confirm zero new routes. All changes are inline additions to the existing Historical mode controls within `TopBar.tsx`, which renders on `/`.

**Canonical home check:** The blueprint's IA explicitly registers the Historical controls as part of the persistent app-shell on `/`: "Historical → symbol search + date + time-window picker (local time, zone label, US-session quick-picks) + replay-speed control." The new local timezone label and quick-pick buttons are placed exactly here — inside `TopBar.tsx`'s `{mode === "historical" && ...}` branch (confirmed at `TopBar.tsx:204`). Canonical home is honored.

**Reachability check:** The quick-picks and timezone label are revealed by selecting "Historical" in the `DataSourceSelector` component, which is rendered by `TopBar` on `/`. Selecting "Historical" is one click from the app's only route — ≤1 click to access, well within the 2-click limit. Nav file inspected: `apps/frontend/components/DataSourceSelector.tsx` (the `MODES` array includes `{ value: "historical", label: "Historical" }`); `apps/frontend/app/page.tsx` renders `<TopBar>` unconditionally on `/`.

**Duplicate home check:** No second page for Historical controls exists. No parallel shell introduced.

**Step 2 result: No violations.**

---

## Step 3 — Advisory observations

No advisory issues identified. The changes are tightly scoped: the resolution logic lives in one module, consumed by one component, on one route, under the already-registered IA home. Label usage (`Open 9:30 ET`, `Close 16:00 ET`, `Full RTH 9:30–16:00 ET`) is internally consistent. The zone label display falls back gracefully and is always explicit — consistent with the existing `formatMarketTime` display philosophy in the same module.

---

## Summary

| Check | Result |
|---|---|
| Data Contract — row 12 duplicate computation | PASS |
| Data Contract — row 12 non-canonical source | PASS |
| Data Contract — new values vs. existing concepts | PASS (subsumed by row 12) |
| IA — canonical home for Historical controls | PASS |
| IA — reachability (≤2 clicks) | PASS |
| IA — duplicate home | PASS |
| IA — parallel shell | PASS |
| Advisory | None |

**Verdict: COHERENCE-PASS** — no objective violations. The iteration keeps one source of truth for the historical-window resolution (row 12 owner is `apps/frontend/lib/datetime.ts`, sole consumer is `TopBar.tsx`, no duplicate computation), no new routes or nav sections were introduced, and all new UI is placed under the already-registered Historical controls home on `/`.
