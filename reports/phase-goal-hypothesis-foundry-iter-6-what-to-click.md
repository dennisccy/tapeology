# Phase goal-hypothesis-foundry-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-hypothesis-foundry-iter-6
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend (scoped QA rig, already provisioned with the real one-time exhaust run) running at
  `http://localhost:8301`
- No login required
- Known environment quirk: a screenshot taken of the "Runner / Checkpoint" subsection while the
  page is scrolled down can come back blank. If you need a screenshot, first enlarge your browser
  window (or zoom out) so the subsection is fully visible without scrolling.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads, no blank screen or error page.

2. Scroll to the bottom of the page and click the "Hypothesis Foundry" section header
   - **Expect:** The section expands and shows an "Era-Open Baseline" block near the top.

3. Click the "Epoch / Manifest" subsection header (near the bottom of the expanded panel)
   - **Expect:** The subsection expands and shows the epoch id `epoch:afd19e9c11a6534f`.

4. Click the "Runner / Checkpoint" subsection header (directly below "Epoch / Manifest")
   - **Expect:** The subsection expands and shows a green "Real Epoch — not a fixture" banner at
     the top.

5. Read the "First-read lock recorded at:" line inside the "Runner / Checkpoint" subsection
   - **Expect:** A real ISO timestamp is shown (`2026-08-27T06:55:51.071173Z`) — not blank, not
     "not yet run".

6. Read the "Checkpoint:" line
   - **Expect:** The text reads "Checkpoint: 0 of 0" — this is the honest result, since the era's
     one real research plan has zero candidates to evaluate. It is not an error.

7. Read the "Protected/withheld/sealed reads:" line
   - **Expect:** The count shown is "0", displayed in green text — proof no off-limits data was
     touched while running the exhaust pass.

8. Read the last line of the subsection (the completion sentence)
   - **Expect:** The text says "Exhaust complete — every frozen candidate reached a terminal state
     (zero FROZEN_READY variants this epoch — an honest, vacuous completion)."

9. Refresh the page (F5), then re-expand "Hypothesis Foundry" → "Runner / Checkpoint" again
   - **Expect:** All the same values from steps 5–8 reappear identically — this data is read fresh
     from the backend on every page load, not a client-side computation or a one-time fluke.

10. Click the "Sources / Compiler" subsection header (higher up in the same panel)
    - **Expect:** It still expands and shows the pre-existing text "Hashes match — outcome-blind
      compilation proven." — confirming the older Foundry subsections were not disturbed by this
      change.

---

## What "Working Correctly" Looks Like

- The "Runner / Checkpoint" subsection is the sixth item inside "Hypothesis Foundry", sitting right
  below "Epoch / Manifest", and carries the same green "Real Epoch — not a fixture" banner as its
  neighbor.
- Every value inside it (timestamp, hash, "0 of 0", "0" protected reads, "green" freeze integrity,
  "Idle — lock free" runner status) is a real, already-recorded fact — nothing is a placeholder,
  nothing says "loading" or "undefined".
- The "0 of 0" checkpoint and the completion sentence explicitly calling out "zero FROZEN_READY
  variants" are meant to look empty — that is the correct, honest result for this era's frozen
  research plan, not a bug.

## Common Issues

- **Blank page / error screen on `/desk`**: Check that the backend is running (`curl
  http://localhost:8301/research/desk/micro/foundry`).
- **"Runner / Checkpoint" shows "The real exhaust pass has not been run yet"**: This means the
  backend you're pointed at has not been provisioned with the real recorded exhaust ledger (e.g., a
  freshly seeded rig with nothing copied in yet). Confirm you are pointed at the `:8301` scoped rig
  described in the Prerequisites, not a bare fresh backend instance.
- **Screenshot of the subsection comes back blank**: This is a known capture quirk of deep-scrolled
  sections in this environment, not a page bug — enlarge the browser window so the subsection sits
  unscrolled, then capture again.
