# Phase goal-hypothesis-foundry-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-hypothesis-foundry-iter-8
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required
- No seed data needed — the real committed Hypothesis Foundry epoch (11 source records) is already
  present in the repo

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads, no error page or blank screen

2. Scroll down and click the "Hypothesis Foundry" section header
   - **Expect:** The section expands and shows an "Era-Open Baseline" block with backend suite
     counts and a "Referee Module SHA-256" table

3. Click the "Final Summary" section header (it is the first sub-section, directly below the
   Era-Open Baseline block, above "Sources / Compiler")
   - **Expect:** The section expands showing a "Source counts by disposition" list, followed by
     lines "Family count: 0", "Variant count: 0", "Frozen-ready total: 0", "Evidence class:
     historical_exposed_diagnostic", "Freeze integrity: green"

4. Read the sentence just below those lines
   - **Expect:** The text "Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count
     = 0) -- no candidate reached DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN this era." is visible as a
     full sentence, not just a bare "0"

5. Scroll to the "Source detail" list and find the row labeled
   `pilot-study-1-range-wall-failed-aggression` with the badge `ALIASED_PROXY_ONLY`
   - **Expect:** The row is visible with its `source_id` text and disposition badge

6. Click that row's "Canonical provenance" text to expand it
   - **Expect:** The row expands to show a "Mechanism:" line, an "Audit note:" line, a "Direction
     derivation: BLOCKED_DIRECTION" line, and at least one quoted-text line starting with a
     quotation mark

7. Refresh the page (press F5), then repeat steps 2–3
   - **Expect:** The same "Final Summary" values reappear unchanged — confirms the data is read
     from the real backend on every load, not cached client-side state that could go stale

8. With "Hypothesis Foundry" still expanded, click the "Sources / Compiler" section header (one of
   the six older sections, directly below "Final Summary")
   - **Expect:** It still expands and shows its own previously-shipped content with no errors —
     confirms the new Final Summary section did not break the older sections

---

## What "Working Correctly" Looks Like

- "Final Summary" is the very first sub-section you see when you expand "Hypothesis Foundry" — you
  do not need to open any of the other six sections to see the epoch's overall state
- Every number in "Final Summary" (source counts, family/variant/frozen-ready counts, protected-read
  count) is plain text with no "loading…" spinner stuck in place, and the zero-survivor and
  exhaust-complete facts are written out as full sentences, not bare digits

## Common Issues

- **Blank page / error screen**: Check that the backend is running
  (`curl http://localhost:8301/research/desk/micro/foundry` should return JSON, not a connection
  error)
- **"Final Summary" section is missing entirely**: Check that
  `docs/hypothesis-foundry/epoch-manifest.json`, `source-registry.json`, `freeze-record.json`, and
  `freeze-set.json` are all present and committed at HEAD — the panel intentionally shows nothing
  fabricated if any tracked artifact is missing
- **Screenshots taken via a deep-scroll browser tool come back blank**: this is a known environment
  quirk for this panel — use `demo_runner --mode verify` for a reliable screenshot capture instead
