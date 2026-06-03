# Phase N — User-Visible Changes

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now **stop watching** the current ticker by clicking the new **Stop** button in the top bar (next to the "Watching <TICKER>" label) — the screen clears back to the empty/idle state with no further updates.
- Users can now complete the **full watch lifecycle on screen**: enter a ticker → Watch → read the live cockpit → **Stop** → enter a ticker → Watch again, all without reloading the page.
- Users can now **re-watch the same ticker after stopping it** and get a fresh, cold-start read (the cockpit repopulates from scratch — connecting → live → values) rather than a frozen/closed leftover.

---

## What Changed in the Visible UI

- The **top bar** now shows a **Stop** button immediately after the "Watching <TICKER>" label. It appears **only while a ticker is watched** and is absent on the idle screen.
- The Stop button is a restrained **rose ghost** button (rose text + rose border, transparent fill) with hover/focus/active states, matching the design system's rose = stop/sell-side semantic.
- After pressing Stop, the main area switches from the populated cockpit back to the **idle/empty state ("No ticker watched")**, and the connection status dot returns to **idle** — no stale numbers, no frozen last frame remain on screen.

---

## What Old Behavior Changed

- **Ending a watch:** previously there was no way to deliberately end a watch — the cockpit stayed populated (eventually showing a `closed` status when the bounded sim stream exhausted) until the user navigated away or entered a new ticker. Now the user can explicitly Stop, which both tears down the backend engine and returns the UI to the clean idle state on demand.

---

## Not Visible Yet

- None. The `DELETE /watch/{ticker}` backend endpoint added this iteration is fully wired to the Stop button — there is no backend capability left unexposed in the UI.
