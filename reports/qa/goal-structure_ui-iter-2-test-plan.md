# goal-structure_ui-iter-2 Functional Test Plan

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

On the `/structure` page, users can see the strategy registry (`v1` and `structure_tape` with their config-owned parameters) and the badged founding champion, read verbatim from `GET /research/strategies` and `GET /research/profiles`. J-01's levels/zones surface is independently re-verified as passing with the empty-state overlay fix.

## Test Cases

### TC-01 — Registry Section Renders with Correct Strategy Cards

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running and serving `GET /research/strategies`
- Page load completes without errors

**Steps:**
1. Navigate to `/structure` page
2. Wait for Registry section to load below the Levels & Zones section
3. Inspect `v1` strategy card for entry rule and exit fields
4. Inspect `structure_tape` strategy card for entry rule and exit fields
5. Verify `structure_tape` card displays `stop_bps_by_class`, `r_multiple_by_class`, `size_multiple_by_class`

**Expected outcome:**
- Registry section renders with two distinct strategy cards
- Each field on the cards matches `GET /research/strategies` payload byte-for-byte
- `v1` card shows: entry rule, `r_stop`, `state_flip`, `horizon_seconds`
- `structure_tape` card shows: entry rule, `r_stop`, `reward_target`, `state_flip`, `horizon_seconds`, plus three class-scaled maps
- No fabricated or missing values

**Pass criteria:**
- All rendered values match API response verbatim (use `curl http://localhost:3000/api/research/strategies | jq .strategies` for comparison)
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-01-registry-cards.png`

---

### TC-02 — Champion Badge Shows Correct Founding Strategy and Profile

**Type:** browser
**Preconditions:**
- Frontend running
- Backend serving both `GET /research/strategies` and `GET /research/profiles`
- Registry section loaded

**Steps:**
1. On `/structure` page, locate the champion badge in the Registry section
2. Note the displayed `champion.strategy_id` and `champion.profile`
3. Verify the badge shows `v1` / `default`
4. Open browser DevTools or check raw API: `curl http://localhost:3000/api/research/strategies | jq .champion`
5. Verify badge value matches strategies endpoint response
6. Check `curl http://localhost:3000/api/research/profiles | jq .champion` — must be identical

**Expected outcome:**
- Champion badge displays `strategy_id: v1, profile: default`
- Both API endpoints return the same champion object (single source of truth)
- No hardcoded fallback applied if endpoint unavailable

**Pass criteria:**
- `champion.strategy_id === "v1"` and `champion.profile === "default"`
- `GET /research/strategies`'s `champion` field equals `GET /research/profiles`'s `champion` field byte-for-byte
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-02-champion-badge.png`

---

### TC-03 — Registry Unavailable State Renders Honestly

**Type:** browser
**Preconditions:**
- Frontend running
- Backend is stopped or `/research/strategies` endpoint returns non-200 (e.g., 500)
- Page has not yet loaded the Registry section

**Steps:**
1. Stop or mock the backend to return a 500 error on `/research/strategies`
2. Navigate to `/structure` page (or refresh if already loaded)
3. Wait 3 seconds for the Registry section to attempt load
4. Inspect the rendered state

**Expected outcome:**
- Registry section displays an explicit "registry unavailable" state
- No fabricated strategy cards rendered
- No hardcoded `v1`/`default` champion shown
- UnavailablePanel (amber border/bg) is displayed with a distinct message

**Pass criteria:**
- `data-testid="structure-registry-unavailable"` is present
- Message text clearly indicates registry fetch failed
- No `<article>` cards (strategy cards) are rendered
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-03-registry-unavailable.png`

---

### TC-04 — J-01 Re-verify: Levels-but-No-Zones Empty State

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running with no bars recorded at the current as-of date
- `/structure` page with "as-of" form set to a date with no bar data

**Steps:**
1. Navigate to `/structure` page
2. Set the "as-of" date input to a date with no bars (e.g., a weekend or future date)
3. Click "Load" button to fetch levels/zones
4. Wait for StructureChart to render
5. Inspect the rendered output for the empty-state overlay
6. Verify the overlay text reads "No candles to draw at this as-of time."
7. Confirm the overlay has an explicit z-index above the chart area

**Expected outcome:**
- Empty-state overlay renders visibly above the chart canvas
- Text "No candles to draw at this as-of time." is displayed
- No blank white/gray box (chart frame with no content inside)
- Overlay has `z-index: 10` (or higher) to sit above lightweight-charts canvases

**Pass criteria:**
- Overlay is visible and readable (not hidden behind the chart)
- Text message is present and matches spec exactly
- No chart-frame-only state (which would be a critical honest-state violation)
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-04-j01-empty-state.png`

---

### TC-05 — J-01 Re-verify: Populated Levels and Zones Render Correctly

**Type:** browser
**Preconditions:**
- Frontend running
- Backend running with bars and levels/zones recorded
- `/structure` page with an as-of date that has bar data

**Steps:**
1. Navigate to `/structure` page
2. Set the "as-of" date to a date with recorded bars and levels
3. Click "Load" button
4. Wait for chart to render with levels and zones
5. Inspect the StructureChart for rendered levels (horizontal lines), zones (shaded regions), and zone label table
6. Verify that the Confluence zones table shows class labels (A, B, C, etc.) and zone boundaries

**Expected outcome:**
- Chart renders with visible level lines and zone regions
- Zones table displays class names and zone-boundary values
- No regression from iter-1 (layout, colors, responsiveness intact)
- Chart interactions (hover, zoom) work if applicable

**Pass criteria:**
- At least 2 level lines visible on chart
- Zones table populated with rows containing class name and boundary price
- No JavaScript console errors
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-05-j01-populated-levels.png`

---

### TC-06 — fetchStrategies() Unavailable-State API Test

**Type:** api
**Preconditions:**
- Backend running or mocked to return non-200 on `/research/strategies`
- Frontend code has been built and `fetchStrategies()` function exists in `apps/frontend/lib/api.ts`

**Steps:**
1. Simulate a non-200 response from `GET /research/strategies` (e.g., return 500 or close the connection)
2. Call `fetchStrategies()` from the browser console or a test script
3. Capture the returned object

**Expected outcome:**
- `fetchStrategies()` returns `{ ok: false, strategies: null, error: <message> }`
- No exception is thrown
- Behavior mirrors `fetchProfiles()`'s pattern

**Pass criteria:**
- `strategies === null` when endpoint is unavailable
- `ok === false`
- `error` field contains a human-readable message
- No fabricated registry object is returned

---

### TC-07 — Single Source of Truth: Champion Coherence Across Endpoints

**Type:** api
**Preconditions:**
- Backend running
- Both `/research/strategies` and `/research/profiles` endpoints are accessible

**Steps:**
1. Fetch `curl -s http://localhost:3000/api/research/strategies | jq .champion`
2. Fetch `curl -s http://localhost:3000/api/research/profiles | jq .champion`
3. Compare the two objects byte-for-byte (use `diff` or visual inspection)

**Expected outcome:**
- Both endpoints return identical `champion` objects
- `champion.strategy_id === "v1"`
- `champion.profile === "default"`
- No timestamp or computed field divergence

**Pass criteria:**
- The two responses are byte-identical (same JSON structure and values)
- Coherence-auditor confirms no second champion shape in the codebase

---

### TC-08 — No Backend Code Changes (Anti-goal Verification)

**Type:** artifact
**Preconditions:**
- Implementation complete
- `git diff` is available

**Steps:**
1. Run `git diff HEAD~1 apps/backend/` (or `git diff` on the branch against main)
2. Inspect all diffs in `apps/backend/app/research/` and `apps/backend/app/meta.py`

**Expected outcome:**
- No changes to `strategies.py`, `profiles.py`, `routes.py`, or `config.py`
- The `/structure` nav entry in `meta.py` is unchanged (already shipped in iter-1)
- No new endpoint or computation added

**Pass criteria:**
- `git diff` shows zero byte changes in `apps/backend/app/research/*` and `apps/backend/app/meta.py`
- Diff is **frontend-only**: only `apps/frontend/lib/types.ts`, `apps/frontend/lib/api.ts`, `apps/frontend/app/structure/page.tsx`, and possibly `apps/frontend/components/StructureChart.tsx` (if J-01 re-verify requires a fix) are modified

---

### TC-09 — Backend Suite Green and J-04 Regression Check

**Type:** api
**Preconditions:**
- Backend running with full test environment set up
- Python 3.8+ and pytest installed
- No uncommitted backend changes

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee test-output.log`
2. Capture the final summary line (e.g., "1147 passed in 15.23s")
3. Verify `config_fingerprint` is still `4d665603569b9dbf`: `curl -s http://localhost:3000/api/research/meta | jq .config_fingerprint`
4. Check that the SIM-BUYER/SIM-SELLER cockpit flows still settle correctly (existing J-04 surface)
5. Verify 5-link nav is intact on `/` (Home, /journal, /studies, /performance, /structure)

**Expected outcome:**
- All 1147 tests pass (no new failures, no regressions)
- `config_fingerprint` remains `4d665603569b9dbf` (frozen v1 and default profile behavior)
- Cockpit summary/entry-exit flows render correctly
- Navigation links on `/` all respond with 200 status

**Pass criteria:**
- Test run exits with code 0
- Summary shows `1147 passed` (or same baseline count, no new failures)
- `config_fingerprint` value matches expected constant
- No regressions in prior surfaces (`/journal`, `/studies`, `/performance`, cockpit)

---

### TC-10 — Registry Section Loads Independent of Levels Load Button

**Type:** browser
**Preconditions:**
- Frontend running
- Backend serving both `/research/strategies` and `/research/profiles`
- JavaScript enabled

**Steps:**
1. Navigate to `/structure` page
2. Do NOT click the "Load" button for Levels & Zones
3. Wait 2 seconds for auto-load effects to complete
4. Inspect the Registry section (should be visible and populated)
5. Verify the Levels & Zones chart area is still empty/loading

**Expected outcome:**
- Registry section is populated with strategy cards and champion badge
- Levels & Zones chart is still empty (no bars loaded yet)
- Two sections operate independently

**Pass criteria:**
- Registry section is fully rendered and clickable without interacting with the Load button
- `useEffect` hook fetches strategies and profiles on page mount (independent of handleLoad)
- Screenshot captured in `reports/qa/goal-structure_ui-iter-2-evidence/TC-10-registry-auto-load.png`

---

## Summary

**Total test cases:** 10
- **Browser tests:** 5 (TC-01, TC-02, TC-04, TC-05, TC-10)
- **API tests:** 3 (TC-06, TC-07, TC-09)
- **Artifact checks:** 2 (TC-03, TC-08)

**Key verification areas:**
- Registry section renders correctly with verbatim API values
- Champion badge shows founding `v1`/`default` from a single source
- Honest states (unavailable, empty levels-but-no-zones) render explicitly
- J-01 empty-state overlay fix is confirmed visible
- Backend remains unchanged; frontend-only diff
- J-04 regression check confirms no breakage in prior surfaces
