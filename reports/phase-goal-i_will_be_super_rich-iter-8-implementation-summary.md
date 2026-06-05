# Phase goal-i_will_be_super_rich-iter-8 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Written by:** developer

---

## Features Implemented

- **Pick a historical window in your own local time**: When you choose the **Historical** data
  source and enter a date and start/end time, the app now treats those times as **your local time**
  and fetches exactly that window from the data vendor. You no longer have to mentally convert your
  time to UTC. A small label next to the inputs tells you which timezone your entry is read in (for
  example, `Asia/Hong_Kong`).
- **One-click US market-session presets**: Three buttons sit beside the Historical date/time
  controls — **Open 9:30 ET**, **Close 16:00 ET**, and **Full RTH 9:30–16:00 ET**. Click one and it
  fills the start/end window for you. Each button also shows the equivalent time **in your own local
  zone** for the date you picked (e.g. "Open 9:30 ET (21:30 local)"), so you always see both the New
  York market time and your time. The buttons stay disabled until you have chosen a date.
- **Correct across daylight-saving time**: The 9:30 / 16:00 New York anchors are converted using the
  real New York calendar, so a summer date and a winter date map to the correct (different) absolute
  times automatically — there is no fixed offset that could be wrong half the year.

---

## Changed Behavior

- **Historical Watch**: Previously, the date/time you entered in the Historical picker was sent
  without any timezone and the backend interpreted it as **UTC** — so to watch the 9:30 ET market
  open you had to type 13:30 (or 14:30 in winter) yourself, and there was no timezone label and no
  presets. Now the picker interprets your entry as **your local time**, converts it to the exact
  absolute instant, and fetches that — what you pick is what you get.

---

## Backend-Only Items

- None. No backend feature was added. (A backend **test** was added to lock in the timezone
  contract, but it changes no behavior and is not user-facing.)

---

## Incomplete Items

- **Real-historical chart screenshot (J-18)**: The chart that draws real replayed prices as
  candlesticks with tape-state markers was already built and proven by data tests in earlier
  iterations. This iteration adds **no code** to it; the remaining step is for the QA stage to
  capture an actual screenshot of the populated chart (watching the committed Ford sample window) to
  formally mark it "passing". That is a verification step, not unfinished development.
- **Live-vendor confirmation of the timezone fix**: As with the other live-data journeys, confirming
  the corrected window against the real vendor during market hours is an operator-gated check. The
  correctness of the conversion itself is fully verified offline (backend test + a timezone math
  check).

---

## Config and Environment Changes

- None. No new environment variables, config files, or settings. (The 9:30 / 16:00 ET session times
  are fixed display presets in the frontend code, not configuration.)

---

## Known Limitations

- **There is no automated test runner for the frontend** in this project (only a build/type-check
  step), so the timezone conversion is verified by a backend test, a one-off timezone math check, and
  browser QA — rather than a frontend unit-test suite. Adding such a suite was out of scope for this
  change.
- **Far-east timezones and the overnight US session**: For operators many hours ahead of New York
  (e.g. Hong Kong), the US trading session can fall across two of **their** calendar days (the 4:00pm
  ET close is early the next morning locally). The one-click presets handle this correctly because
  they remember the exact absolute window. If you instead type times **manually** in such a zone, the
  app uses the single date you selected — which is the expected manual behavior, and is exactly why
  the one-click presets exist for the common case.
