# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-17 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. This iteration added no user-facing capability by design.

---

## What Changed in the Visible UI

- Nothing changed in the visible UI. All five panels of the cockpit (chart with Control marker, observations, event log, confidence, and tape state), every route, every navigation element, and every form remain identical to the previous iteration. The browser regression sentinel (J-68, SIM-BUYER no-thesis) is expected to produce pixel-identical results.

---

## What Old Behavior Changed

- None. The engine now computes refresh scores faster on long, dense streams, but it produces exactly the same numbers as before. From a user's perspective, the cockpit reads, confidence values, and feature outputs are unchanged. This was verified via a live `POST /watch/SIM-BUYER` + `GET /tape/SIM-BUYER/state` check that still resolved to `buyer_control` at the same confidence as before the change.

---

## Not Visible Yet

- **Engine performance improvement (capability 34):** The tape-reading engine now processes a 10-minute real market recording ~18× faster than before (from ~184 s to ~10 s for the dense-fixture replay). This improvement is entirely internal and has no exposed control or display in the UI.
- **Replay studies capability (J-60–J-62):** This iteration's engine gate is the prerequisite for the upcoming `/studies` page and study-runner API. Neither the studies page, the studies API, nor any navigation link to it exists yet — that surface lands next iteration.
- **Committed real-market test recording:** A 10-minute PG (Procter & Gamble) SIP fixture (2026-06-09, ~1.2 MB) is now committed in the test suite and will be reused as the reference study next iteration. It is a test/CI asset only; no part of it is displayed to users.
- **CI timing gate:** An automatic speed check (`dense_replay_time_budget_seconds = 60.0`) is now enforced in the test suite. It is a CI gate value only and does not affect any displayed analytics grouping or research record.
