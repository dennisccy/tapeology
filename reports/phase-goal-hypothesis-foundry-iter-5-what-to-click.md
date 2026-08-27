# Phase goal-hypothesis-foundry-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-hypothesis-foundry-iter-5
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required — this is a read-only operator surface
- No seed data needed — the real epoch this guide checks for is already generated and permanently committed to the repository (Git commit `dff64eaa`)

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads with no blank screen and no error banner

2. Scroll down and click the "Hypothesis Foundry" section header
   - **Expect:** The section expands, showing an "Era-Open Baseline" block and a "Source registry hash:" line with a long hex value (NOT the text "not_yet_generated")

3. Click the "Sources / Compiler" row header (first of five rows under Hypothesis Foundry)
   - **Expect:** The row expands showing an amber "Hermetic Fixture — not the real epoch" banner and a list of exactly 8 fixture rows, including both `fixture-variant-a` and `fixture-variant-b` as separate entries, each showing "Operative formula refs:", "Superseded fields:", and "Aliases/lineage ids:" lines

4. Click the "Hermetic Oracles" row header (fourth row)
   - **Expect:** The row expands showing 7 lines under a list pairing outcome labels with states (e.g. "fragile → EVALUATED_KILLED"), plus a "Best-of-N disclosure: n_variants_tried=7 · threshold_bps=..." line

5. Click the "Epoch / Manifest" row header (fifth and last row, directly below Hermetic Oracles)
   - **Expect:** The row expands showing a distinct emerald/green banner reading "Real Epoch — not a fixture" (visibly different color from the amber banners in step 3)

6. In the expanded Epoch / Manifest panel, read the "Status:" line
   - **Expect:** Reads "Committed — Git-visible pre-outcome barrier crossed" in green text, and an `outcome_access_census: 0` line also in green text

7. Scroll down within the same panel to "Source dispositions (11 of 11 required objects)"
   - **Expect:** Exactly 11 rows are listed underneath, each showing a source id and a disposition (e.g. `EXCLUDED_GATE_CLOSED`, `ALIASED_PROXY_ONLY`, `BLOCKED_DIRECTION`)

8. Continue scrolling to "Compiled families (0)"
   - **Expect:** The text "Zero compiled candidates this epoch — every required source disposed non-COMPILED." is shown — this is the correct, expected result, not an error

9. Refresh the page (press F5 or Cmd+R), then repeat steps 2 and 5
   - **Expect:** All the same values from steps 6-8 reappear identically — confirms the real epoch is durably stored (committed to Git), not session-only

10. Navigate to `http://localhost:3301/` (Cockpit) and then to `http://localhost:3301/structure`
    - **Expect:** Both pages load normally with their usual charts/panels — confirms this phase's Foundry-only changes did not break the rest of the app

---

## What "Working Correctly" Looks Like

- The Epoch / Manifest panel shows a green "Real Epoch — not a fixture" banner that looks visually different from the amber "Hermetic Fixture" banners on the other four Foundry subsections
- All 11 source dispositions are listed, and none of them is missing or shows a blank/undefined value
- The empty "Compiled families (0)" state is shown as readable text, not as a blank gap or a red error

## Common Issues

- **Blank page / error screen on `/desk`**: Check that the backend is running (`curl http://localhost:8301/research/desk/micro/foundry`)
- **"Source registry hash:" still shows "not_yet_generated"**: The backend process may need a restart to pick up the committed files — module-level reads happen once at process start, not per request
- **Epoch / Manifest banner looks the same amber color as the others**: This would indicate a real regression — the two banners must use different colors (emerald vs. amber) so operators can never confuse a real epoch with a fixture demo
