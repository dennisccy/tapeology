# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Navigate to the Studies page by clicking the "Studies" link in the top navigation bar (previously it was greyed out and unclickable).
- Create a replay study by clicking "Run study" on the Studies page after choosing a source (the committed PG reference window, a seeded sim scenario, or a real symbol + past date/time window), a setup type, and a direction.
- Watch a study's status update in real time from Queued to Running to Done without refreshing the page — the job list polls automatically while any study is active.
- Cancel a queued or running study by clicking the "Cancel" button on its row in the job list.
- Read per-study results by clicking a row in the job list: occurrence arm times, verdict summaries, and R bases are shown in an occurrences table; ternary excursion counts per horizon (+1R / −1R / neither / truncated separately) are shown in a distribution block.
- Compare how the setup's occurrences performed side-by-side with a seeded random-arm-time null baseline — both panels show the same horizons so the comparison is direct.
- Re-run an identical study from the results view using the "Re-run identical" button, producing the exact same numbers (the baseline seed is re-used).
- Read honesty stamps on every completed study: the data feed, config fingerprint, and baseline seed are visible in the results header so the user knows exactly what configuration produced the numbers.
- Supply a manual level price for "level break" and "failed move fade" setups; the form shows a hindsight warning inline and the level is labeled in the results as chosen with hindsight and excluded from any cross-study comparison.

---

## What Changed in the Visible UI

- The "Studies" item in the top navigation bar changed from a grey, disabled, non-clickable label (with a "Coming with replay studies" tooltip) to a fully active link that navigates to `/studies`.
- A new `/studies` page exists with a two-column layout on wide screens: the left column contains the create form and job list; the right column displays the selected study's results.
- The create form (`StudyCreateForm`) has three mutually exclusive source options presented as large radio-style cards: "Reference window (committed PG SIP fixture — no credentials)", "Seeded sim scenario" (with a dropdown of SIM-REVERSAL, SIM-BUYER, SIM-SHIFT, SIM-SELLER), and "Symbol + past window" (with a symbol search field, a dd-MM-yyyy date input, start/end time inputs, and three time-range preset buttons: Open 9:30 ET, Close 16:00 ET, Full RTH).
- The create form shows a level price input and an amber hindsight-warning box only when the selected setup is "level break" or "failed move fade" — the input is hidden for all other setup types.
- The "Run study" button is disabled until all required fields for the chosen source are complete; it changes to "Running…" while the request is in flight.
- The job list (`StudyList`) shows each study as a row with a colored status badge (slate for Queued/Cancelled, amber for Running, rose for Failed, neutral slate for Done), the setup name and direction, the data source and feed badge, a "Hindsight level" amber chip where applicable, and an event-processed counter while running.
- A "Cancel" button appears on each row whose status is Queued or Running; it disappears once the study reaches a terminal state.
- The results panel (`StudyResultsView`) renders two side-by-side distribution blocks (Your setup / Random-time baseline), each showing per-horizon rows with four explicitly separated counts: +1R (emerald), −1R (rose), neither (slate), and Truncated (amber). The truncated count is always its own chip — it is never folded into the other three.
- The results panel shows an occurrences table with columns "Arm time (logical s)", "Verdict reached", and "R basis" — all numeric values in monospace font.
- Feed, config fingerprint, and baseline seed stamps appear in the results header in monospace chips; the config fingerprint has a title tooltip with the full value.
- A "Descriptive only — not trading advice" framing line appears near every set of figures; a separate measurement-framing paragraph appears at the page header and again at the foot of the results view.
- Non-terminal studies show their own per-status absence sentence instead of results (Queued and Running each have distinct text — not shared); a Failed study shows its explicit error message in rose; a Cancelled study shows a PARTIAL warning above any partial results.

---

## What Old Behavior Changed

- Studies nav entry: previously rendered as a `<span>` with `aria-disabled="true"` and cursor-not-allowed styling (non-interactive). It now renders as a `<Link>` with full hover/focus/active states and navigates to `/studies`. This is the only change visible from existing pages (Cockpit, Journal).

---

## Not Visible Yet

- Arbitrary-window historical studies (Symbol + past window source) require valid market-data credentials in the server environment. Without credentials the backend returns an explicit "provider unavailable" 422; the form itself is fully rendered and submittable. Live end-to-end verification of this path was not performed in this iteration.
- Background jobs are process-scoped: a study left in the "Running" state by a server restart remains visibly "Running" in the list and is not auto-resolved to a terminal state. The UI renders it honestly in its stored state; a future iteration may add a startup sweep.
