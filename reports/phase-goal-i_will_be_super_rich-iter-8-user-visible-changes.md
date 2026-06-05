# Phase goal-i_will_be_super_rich-iter-8 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now pick a Historical window in their **own local timezone** — no manual UTC conversion required. Enter a date and start/end times in the Historical picker and the app converts them to the correct absolute instant automatically.
- Users can now one-click the **Open 9:30 ET** button to fill the start/end window for the US market open, shown alongside its local-time equivalent for the chosen date (e.g. "21:30 local" in Hong Kong).
- Users can now one-click the **Close 16:00 ET** button to fill the start/end window for the US market close, annotated with its local equivalent.
- Users can now one-click the **Full RTH 9:30–16:00 ET** button to fill the complete regular-trading-hours window in one action, with both local-equivalent times shown.
- Users can now see at a glance which timezone their Historical time entries are being interpreted in, via the timezone label displayed beside the date/time inputs (e.g. `Asia/Hong_Kong`).

---

## What Changed in the Visible UI

- The **Historical mode controls** in the top bar now include a small muted monospaced timezone label adjacent to the start/end time inputs (e.g. `Asia/Hong_Kong`), with a tooltip "Your date and time entry is interpreted in this timezone".
- A new row of three **US-session quick-pick buttons** — "Open 9:30 ET", "Close 16:00 ET", "Full RTH 9:30–16:00 ET" — appears in the Historical mode controls beside the date/time/speed inputs. Each button shows the local-equivalent time for the chosen date. The buttons are visually disabled (40% opacity, not-allowed cursor) until a date is entered.
- Each quick-pick button displays a local-time annotation alongside the ET label (e.g. "Open 9:30 ET (09:30 PM local)") so the user sees both the New York time and their own time simultaneously.

---

## What Old Behavior Changed

- **Historical Watch time resolution**: Previously, date/time values entered in the Historical picker were sent without a timezone offset, causing the backend to silently treat them as UTC — operators had to hand-convert their local time to UTC before entering (e.g. type "13:30" to watch the 9:30 ET open). Now, the times entered are treated as the operator's local time and resolved to the exact absolute UTC instant before the request is sent. What the user types locally is what gets fetched.
- **Historical Watch POST body**: Previously, the `start` and `end` fields in the POST body were naive strings like `2026-06-02T15:00`. They are now tz-aware UTC ISO-8601 strings like `2026-06-02T15:00:00.000Z` — the exact resolved instant.
- **Quick-pick state on manual edit**: If a user clicks a quick-pick and then manually edits the date, start time, or end time fields, the quick-pick selection is cleared and the manual entry takes over. This ensures the submitted window always reflects exactly what the user typed.

---

## Not Visible Yet

- **Backend timezone contract test** (`test_window_resolution.py`): Six new backend unit/integration tests assert the correct UTC resolution for offset-bearing and naive inputs. These are verification tests — no new API behavior or endpoint was added; they are invisible to the user.
- **J-18 real-historical chart render verification**: The real-historical candlestick chart (real replayed Ford prices with tape-state markers) exists in the application from prior iterations. This iteration adds no chart code — the remaining step is browser-QA capturing a populated screenshot of that chart to formally mark J-18 as passing. The chart itself is accessible via the Historical mode picker.
