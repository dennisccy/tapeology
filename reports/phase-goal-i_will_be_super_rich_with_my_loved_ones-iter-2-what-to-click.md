# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000` (verify: `curl http://localhost:8000/health` should return 200)
- No login required — the app is unauthenticated
- No seed data required — SIM-BIDABS is a built-in simulated ticker

---

## Verification Steps

1. Navigate to `http://localhost:3650` in your browser
   - **Expect:** The cockpit page loads. You see a ticker input area. No error page or blank screen.

2. Start a watch on SIM-BIDABS: type `SIM-BIDABS` in the ticker input field and click the watch/start button. Wait up to 20 seconds for the cockpit to settle.
   - **Expect:** The price chart (candlestick chart) appears at the top and begins updating. Below it, the feature panels and event log populate with live data. At this point — and NOT before — a single horizontal bar appears between the price chart and the panel grid, containing the text "Declare a thesis on this ticker to watch the tape judged against it." and a "Declare thesis" button.
   - **Broken looks like:** The thesis strip bar appears while the page still shows "Connecting…" or "Waiting for first event" — it should remain invisible until the cockpit is fully settled.

3. Click the "Declare thesis" button in the thesis strip.
   - **Expect:** The form expands inside the strip. You see a "Setup" dropdown, a "Direction" dropdown, an "Invalidation" price input, a "Declare" button, and a "Cancel" button. The options in the Setup dropdown include "Absorption Reversal", "Trend Continuation", "Level Break", and "Failed Move Fade" — populated from the backend, not hardcoded.
   - **Broken looks like:** The text "Loading the setup catalog…" persists indefinitely, or the form shows no options in the Setup dropdown.

4. In the "Setup" dropdown select "Level Break". Observe the form.
   - **Expect:** A "Level" price input field appears immediately below the existing fields. Change the Setup back to "Absorption Reversal" — the Level field disappears immediately.
   - **Broken looks like:** The Level field does not appear for Level Break, or it appears for Absorption Reversal when it should not.

5. With "Absorption Reversal" selected and "Long" selected in Direction, note the current last price shown in the price chart. Type a price that is BELOW that last price into the "Invalidation" field (e.g., if last price is 100.00, type `98.00`). Click "Declare".
   - **Expect:** The button briefly shows "Declaring…" and is disabled. The form closes. The strip expands to show the active thesis: setup name, the direction "Long" in green (emerald), the invalidation price in monospace font, a bulleted list of expected-behaviour statements each with a colored status dot ("met" / "not yet" / "violated"), a grey "Pending" badge, and a footer with source/feed stamp and "Descriptive only — not trading advice."
   - **Broken looks like:** The form does not close, the strip stays in idle state, or the active display is missing the statement list or the "Pending" badge.

6. Observe the statement status dots in the active thesis display for 30–60 seconds without refreshing.
   - **Expect:** At least one status dot changes color or label (between "met", "not yet", "violated") as the SIM tape advances. The price chart and feature panels continue updating normally alongside the thesis strip — nothing else on the page stops or freezes.
   - **Broken looks like:** All status dots remain completely static for over 2 minutes, or the price chart stops updating after the thesis is declared.

7. Click the browser's refresh button (F5 or Cmd+R) while an active thesis is showing.
   - **Expect:** After refresh, the cockpit re-establishes the watch on SIM-BIDABS. Once settled, the thesis strip returns to the IDLE state (single bar with "Declare thesis" button) — the previously declared thesis is no longer shown because a fresh stream session starts. This is expected behavior for this iteration.
   - **Broken looks like:** The page crashes, shows a blank screen, or the thesis strip errors out on reload.

8. With the cockpit settled and the thesis strip in idle state, scroll down the page to see all cockpit panels.
   - **Expect:** The cockpit panel grid is fully visible below the thesis strip. All feature panels, the event log, and the tape state panel are present and not clipped or misaligned. The thesis strip occupies a single line height and does not push any panel off-screen.
   - **Broken looks like:** Any cockpit panel is shifted, hidden, or overlapped by the thesis strip.

---

## What "Working Correctly" Looks Like

- After declaring an absorption_reversal / long thesis with a valid invalidation price, the strip shows: the setup name, "Long" in green, the invalidation price in a fixed-width (monospace) font, a bulleted list with at least 2–3 statements and colored status dots, a grey "Pending" badge, and the source/feed footer.
- The statement status dots change colors in real time as the SIM tape progresses — without a page reload.
- The cockpit panel grid below the thesis strip is unaffected: chart still ticks, feature panels still update, event log still appends rows.

## Common Issues

- **Thesis strip not appearing after cockpit settles:** Confirm the stream has fully settled — the feature panels should show numeric values, not placeholder dashes. If the stream is stuck at "Connecting…", check that the backend is running (`curl http://localhost:8000/health`).
- **"Loading the setup catalog…" never resolves:** The backend taxonomy endpoint may be down. Check `curl http://localhost:8000/research/taxonomy` — it should return JSON with a `setups` array.
- **Declare button stays on "Declaring…" indefinitely:** The backend POST may have timed out or returned an unexpected error. Check the browser console (F12 → Console) for a network error on `/research/thesis`.
- **Wrong-side invalidation not showing an error:** If you enter an invalidation price above the current last for a Long thesis and the form submits without error, this is a bug — the strip should show a rose error message and NOT create the thesis.
