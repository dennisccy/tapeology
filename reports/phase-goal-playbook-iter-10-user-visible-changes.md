# Phase goal-playbook-iter-10 — User-Visible Changes

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/desk`'s **Playbook Signals** section, after opening the detail of a `range_trade` signal
  that was computed by this iteration's code (i.e. any `range_trade` signal detected from now on),
  users can see one more fact about the setup: whether the price swing leading into the trade
  turned back around right at the middle of the tested range (the book's own "midrange rule"),
  shown next to the existing "crossed midrange" note. This is purely informational — it never
  changes which signals appear, how they are ranked, or anything else about the record.

That is the only new capability this iteration adds. No new button, form, page, or navigation
entry was added.

---

## What Changed in the Visible UI

- The `range_trade` signal detail line on `/desk` — the one that reads "range … MBR wide · low
  zone touches … · high zone touches … · broke at slot …" inside a selected signal's detail card
  — can now include one more optional clause: **" · turned at midrange"**, appended immediately
  after the existing **" · crossed midrange"** clause and before **" · absorption bar present"**.
  Same small gray inline-text styling as its neighbors (`text-[11px] text-slate-500`); no new
  visual element, color, icon, or layout change.
- This line only ever appears for signals whose `setup_id` is `range_trade`, and the new clause
  only appears when the underlying value is `true` — exactly like the two chips it sits beside.

---

## What Old Behavior Changed

None. Every `range_trade` signal recorded before this change shipped renders exactly as it did
before — the new clause simply does not appear on those records, the same way any other optional
field on this page behaves when absent. This was verified directly: the currently-running app's
one on-file `range_trade` signal (symbol `RTAAA`, session 2026-06-22, computed by this iteration's
own code) shows the pre-existing "crossed midrange" clause unchanged and no other rendering
difference — only the new field's own presence/absence controls whether the new clause shows.

---

## Not Visible Yet

- **Nobody has yet seen the new clause actually appear on screen.** The underlying logic is proven
  correct by a backend test (`test_range_trade_turned_at_midrange_true_and_its_near_miss_control`
  in `apps/backend/tests/test_desk_playbook_detect.py`, a hand-built example plus a near-miss
  control), and the field is confirmed to be wired end-to-end into the API response and the page —
  but on the app instance available for this analysis (backend at `:8301`, universe
  `source_url: "fixture-rig-iter8-replay"` — the same scoped fixture rig `browser-qa-agent` uses
  for this iteration's formal check), the only reachable `range_trade` signal (`RTAAA` on
  2026-06-22) evaluates the new field to `false`. That signal's own bars were not touched by this
  iteration (confirmed in the seed script's own change notes), so this is not a fluke of timing —
  the SAME rig will show the SAME `false` result to `browser-qa-agent` unless a new date/fixture is
  computed. Whoever performs the next browser check should expect that producing a screenshot with
  the clause actually visible may require a fresh Playbook compute on a not-yet-recorded session
  (with no guarantee any given date's `range_trade` signal, if one even fires, will satisfy the
  "turned at midrange" condition) rather than simply reloading `/desk`. This is a completeness gap
  in currently-available evidence, not a functional defect — see the UI Test Plan (UT-03) for the
  exact procedure to run as soon as a qualifying example exists.
- The four documentation-only edits to `docs/playbook-detector-spec.md` (spec wording corrected to
  match already-shipped code, plus the disclosures-clause split) are internal engineering
  documentation only — they were never going to be, and are not, visible anywhere in the product UI.
- The scoped test rig's `/structure` chart now renders real AAPL candles instead of a blank canvas
  (the `seed_playbook_iter8_replay_rig.py` index-repair fix) — but this only affects the internal
  automated-test copy of the app used for QA. The real, production `/structure` page's AAPL chart
  was never broken for actual users; this fix has no bearing on anything a real operator has ever
  seen.
