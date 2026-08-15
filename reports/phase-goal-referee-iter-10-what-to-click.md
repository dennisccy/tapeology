# Phase goal-referee-iter-10 — What to Click (Operator Verification Guide)

**Phase:** goal-referee-iter-10
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login needed (this project has no auth gate)
- If the page looks unchanged after this round's build, run `rm -rf apps/frontend/.next` and
  restart the frontend dev server — this project's known stale-build gotcha
- Steps 1–5 and 8–10 below are read-only and safe to run anytime. Step 6 (null-build /
  evaluation trigger) is marked **[OPTIONAL — real write]**: it starts a genuine, heavy compute job
  and appends a permanent row to a run ledger with no delete path. Do it only intentionally,
  ideally against a disposable/fixture-scoped backend. Step 7's adjacent "Confirm Registration"
  button (pre-existing, one section above) is the same kind of real, permanent write — do not
  click it as part of this guide.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" page loads, no error page, no blank screen.

2. Scroll to the very bottom of the page
   - **Expect:** Three section headers appear in this order: "Referee Registry", "Referee
     Adjudications", "Referee Runs" — with "Referee Runs" as the last thing on the page.

3. Click the "Referee Adjudications" section header
   - **Expect:** The section expands (its arrow flips from "▸" to "▾"), showing a paragraph
     starting "Referee verdicts are statistical statements about recorded history under stated
     assumptions..." followed by either the text "No hypotheses registered." or a table with
     columns Hypothesis / Verdict / Status / Provenance / Fragility triggers.

4. If the table has any rows, read the "Verdict" column for the first row
   - **Expect:** A plain, uncolored pill showing one of exactly these seven words:
     `registered`, `pending_forward_confirmation`, `insufficient_sample`, `fragile`,
     `no_evidence`, `corroborated`, `basis_retired` — never a blank cell or a made-up label.

5. Click the "Referee Runs" section header (directly below "Referee Adjudications")
   - **Expect:** The section expands, showing a "Null Builds" sub-heading with either "No
     hypotheses registered — nothing to build a null for yet." or one or more boxes each with a
     "Build Null" button, then an "Evaluations" sub-heading with the same shape but "Evaluate"
     buttons and either "No hypotheses registered — nothing to evaluate yet." or one box per
     hypothesis.

6. **[OPTIONAL — real, heavy compute]** To verify the compute path actually works: click any
   "Build Null" or "Evaluate" button that is not already running
   - **Expect:** The button immediately relabels to "Building…" / "Evaluating…" and disables, a
     pulsing-dot progress line showing a growing `<done> / <total>` count appears with no page
     reload, and a "Cancel" button appears beside it. Leave it running or click "Cancel" to stop
     it early — either way, do not force-kill the backend process while it runs.

7. Refresh the page (F5), re-expand "Referee Runs", and look below the button you clicked in step 6
   - **Expect:** If the run you started in step 6 has finished, a new row appears in the run
     ledger table below the controls showing that run's id, its state, and its start/finish
     times. If it is still running, its live progress line reappears in the same place after the
     section re-expands (a stale-page reload does not lose the run itself, only its live
     progress display until you look again).

8. Scroll up and click the "Referee Registry" section header (directly above "Referee
   Adjudications")
   - **Expect:** It still expands and shows its existing 5-row shortlist table and "Registered
     Hypotheses" table exactly as before this round — confirms the two new sections below it
     didn't break it. Do NOT click "Select" or "Confirm Registration" here — that button performs
     an unrelated real, permanent write and is out of scope for this guide.

9. Scroll further up and click the "Playbook Evidence" section header (above "Referee Registry")
   - **Expect:** It still expands and shows its existing content unchanged — confirms none of
     this round's changes disturbed a section that existed before this era's Referee work.

10. Navigate to `http://localhost:3301/` (the cockpit page)
    - **Expect:** The cockpit page loads with its chart visible, no error page — confirms this
      round didn't regress the product's other kept pages.

---

## What "Working Correctly" Looks Like

- "Referee Adjudications" and "Referee Runs" both sit below "Referee Registry", collapsed by
  default, expandable with one click each — no separate menu or hidden URL needed to find them.
- Every verdict shown is one of the exact seven vocabulary words, rendered as plain uncolored
  text/pill — this product deliberately never colors a verdict to imply advice.
- A compute trigger's progress updates live on the page without ever needing a manual refresh,
  and a finished run always leaves a permanent row behind in its ledger table.
- Nothing above "Referee Adjudications" on the page looks any different than it did before this
  round.

## Common Issues

- **Blank page / error screen**: Check that the backend is running —
  `curl http://localhost:8301/health` should return `{"status":"ok"}`.
- **New "Referee Adjudications"/"Referee Runs" sections are missing, or the page looks exactly
  like before**: the frontend is likely serving a stale build. Run
  `rm -rf apps/frontend/.next`, then rebuild/restart the frontend dev server.
- **A "Build Null"/"Evaluate" button's progress line never seems to move**: these are real,
  heavy compute paths capped by this host's CPU-mask guard — they can take a while even against a
  small fixture corpus. Do not force-kill the backend with a pattern-based process kill (this
  host is shared with other, unrelated projects) — stop it by its exact PID only, and only if you
  started it yourself for this check.
- **A trigger button shows a red "Refused —..." message**: expected if a run for that exact null
  spec or hypothesis is already in flight (e.g. from another browser tab, or a previous click) —
  this is the single-flight guard working correctly, not a bug.
