# Phase goal-fast_wall-iter-1 — User-Visible Changes

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the `/structure` page with confidence that doing so will never silently start an hours-long backend computation. Previously, simply loading the page while the edge-report cache was cold triggered the full multi-hour backtest sweep as an invisible side effect of the page load, pinning the backend near 100% CPU for hours.
- When the edge report genuinely hasn't been computed yet, users now see an honest, prompt explanation — a panel headlined "Edge report not computed yet." with a specific detail line beneath it — instead of an indefinite loading spinner or, worse, no indication at all that a massive background job had just started.
- Users can reload or revisit `/structure` as many times as they like without any risk of re-triggering computation or degrading backend performance for other pages or other users, regardless of whether the edge-report cache happens to be warm or cold.

---

## What Changed in the Visible UI

- The **Edge Report** section on `/structure` (the panel titled "Edge Report" near the bottom of the page) gained a new visible state: a distinct amber-toned panel with the headline "Edge report not computed yet." and a detail line explaining what would need to happen for a report to exist (this text comes verbatim from the server, not a canned frontend message). It appears whenever the cache is cold and at least one dataset has been registered.
- This new panel sits in the same place as, and follows the same visual treatment as, the page's existing degraded/honest-absence panels (the same amber border/background style already used when the backend is unreachable) — no new visual language was introduced.
- Nothing else on `/structure` changed in appearance: no new page, no new navigation link, no new button, no new field displayed anywhere else on the page.

---

## What Old Behavior Changed

- **Opening `/structure` while the edge-report cache is cold**: previously this silently kicked off the full multi-hour backtest sweep in the background of the page load — an expensive, invisible side effect of simply looking at the page, with no warning shown to the user. Now, loading the page never starts that computation. It either shows the already-computed report (if the cache is warm) or the new honest "not computed yet" panel (if cold) — both return promptly.
- **Speed of the Edge Report section, specifically on the real production dataset**: asking for the edge report now answers in roughly 30 seconds (bounded by the time it takes to list what data has been recorded) instead of potentially hours. This is a large improvement but is not yet near-instant — that further speedup is planned for a later update and is not part of this change.
- The previously existing "No edge-report cells yet." message (shown when the cache is warm but the computed report has zero cells) and the populated report table view are unchanged in appearance and continue to behave exactly as before — this update only added a new state that runs *before* those, for the cold-cache case.

---

## Not Visible Yet

- There is still no button, control, or command anywhere in the app that lets a user or operator actually trigger the edge-report computation. The underlying machinery to do so (`compute_and_publish`) is fully built and tested on the backend, but nothing in the running application calls it yet. Until a future update adds that trigger, the Edge Report section will keep showing "not computed yet" whenever the cache is cold — there is currently no way to make it finish computing through the app.
- The not-computed payload also carries a dataset count (how many datasets are registered) and a register disclosure string from the backend, but neither is separately displayed in the new panel this update — the dataset count has no UI slot yet, and the register string is already shown elsewhere (in the populated-report view) rather than duplicated here.
- The Structure page's other slow sections — the recorded-data listing and the Case Studies section — are not sped up by this update. They are pre-existing, already-known slow spots slated for separate future updates, unrelated to the Edge Report fix delivered here.
