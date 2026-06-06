# Phase goal-i_will_be_super_rich-iter-9 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See an immediate "Connecting to \<SYMBOL\>…" acknowledgement on the main cockpit screen (with an amber pulsing dot) the instant they click Watch — in Simulated, Live, and Historical modes — without waiting for the backend to respond.
- Receive a visible, named timeout message ("Market data provider timed out…") in the TopBar error banner when the data provider or backend is slow or unreachable, instead of waiting indefinitely.
- See an explicit "Couldn't connect to the tape stream" error treatment on the cockpit area (rose warning icon, `StreamFailedState` panel) when the initial tape connection fails right after Watch, instead of being left with no feedback.
- Get immediate inline feedback ("Enter a ticker symbol" / "Choose a valid time window") next to the Watch button when the symbol field is empty or the Historical date/time window is missing or invalid — the Watch button is also disabled until input is corrected.

---

## What Changed in the Visible UI

- The cockpit area on `/` now shows a new "Connecting to \<SYMBOL\>…" state (amber pulsing dot, symbol name called out) immediately after clicking Watch, before any tape data arrives. Previously the idle screen remained visible until the backend responded.
- The TopBar status dot now includes a `failed` state (rose color, "failed" label) in addition to its existing idle / connecting / live / closed states. This appears when the initial connection to the tape stream fails.
- A new `StreamFailedState` panel (rose ⚠ warning, "Couldn't connect to the tape stream" heading, "Try Watch again" instruction) appears in the cockpit area when the tape stream connection fails before any snapshot arrives. Previously no failure state was shown for this condition.
- An inline amber validation message appears directly beside the Watch button when the symbol is empty/whitespace or when the Historical time window is invalid. The Watch button is grayed and disabled in this state. Previously submitting an empty ticker or invalid window was a silent no-op.
- The inline validation message clears automatically as soon as the user types in the offending field, without requiring a new submission attempt.
- The TopBar error banner now also shows timeout-specific messages such as "Market data provider timed out…" when the watch request takes too long, in addition to its existing error messages.

---

## What Old Behavior Changed

- **Clicking Watch on an empty symbol**: Previously nothing happened (silent no-op). Now the Watch button is disabled until a non-whitespace symbol is entered, and an attempt via keyboard still shows "Enter a ticker symbol" inline.
- **Clicking Watch with a missing or invalid Historical time window**: Previously nothing visible happened. Now the Watch button is disabled and shows "Choose a valid time window" inline until the window is corrected.
- **Watch with a slow or hung backend/provider**: Previously the screen stayed in its current state indefinitely with no user feedback. Now the backend caps each outbound vendor request (8 seconds) and the browser caps each watch request (12 seconds); either cap produces a visible error message instead of an infinite wait.
- **Failed initial tape connection (e.g. backend stops after Watch)**: Previously the initial snapshot fetch failure was silently discarded, and the screen could remain stuck showing "Connecting…". Now a `StreamFailedState` panel and the error banner appear within a bounded time.
- **The idle screen after clicking Watch**: Previously persisted until the backend replied. Now the cockpit area transitions to "Connecting to \<SYMBOL\>…" synchronously the instant Watch is clicked, in all three modes.

---

## Not Visible Yet

None. All implemented backend capabilities (`provider_timeout` error reason, per-call vendor timeout) are surfaced in the UI via the existing error banner and the connecting/failed states.
