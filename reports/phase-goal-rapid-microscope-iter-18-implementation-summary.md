# goal-rapid-microscope-iter-18 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-18
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **The sealed-shard "pass/fail" judge now owns its own minimum sample size.** Previously, the
  internal rule that decides whether a candidate mechanism's one-time sealed test "passes" could
  be handed a caller-supplied minimum sample size — which an iteration-17 audit proved could be
  set as low as 1, letting a single data point be certified as a permanent "pass" under a record
  that claimed a much stricter standard had been applied. This is now impossible: the rule fixes
  its own minimum (30 real data points) and refuses outright to run at all if anything tries to
  hand it a different number.
- **Honest labeling of what does not apply.** The permanent record of each sealed test now
  explicitly states, in plain words, that "session breadth" and "symbol breadth" checks do not
  apply at this stage (rather than silently showing a misleading number like "1").

## Changed Behavior

- **The sealed-evaluation rule (internal, not yet reachable by any real data)**: Previously, a
  caller could narrow or widen the sufficiency requirement for a sealed-shard verdict. Now, the
  requirement is fixed at 30 observations, period — no caller input is ever consulted for it, and
  attempting to supply one is refused before any result is produced.

## Backend-Only Items

- The rewritten rule (`app/research/micro_sealed_evaluation.py`) — no UI wiring exists for it yet,
  by design (this whole capability is not reachable through the product surface until a future
  iteration records real sealed vault data; production currently has zero registered vault
  universes and zero sealed shards).
- `GET /research/desk/micro/graduation` — the one already-existing read-only endpoint this rule
  feeds. No new endpoint, no new page, no UI surface change this iteration.

## Incomplete Items

None from this iteration's own scope — every item in the plan (the rule rewrite, the seven traps,
the two small coverage-gap tests, the QA-only demo fixture) is complete and verified.

One item from the ORIGINAL plan was substituted for an equivalent, for a documented architectural
reason: a stored "golden replay script" for the graduation page was named as an option, but this
route has never had one and cannot have one — its only address is a raw backend URL, and the
automated replay tool that plays back stored scripts is hard-wired to always visit the product's
front-end address instead, so it cannot express "visit the backend directly." This was already
known and recorded before this iteration started. In its place, this iteration adds a small demo
fixture so a human (or the browser-QA reviewer) checking that raw address on the test rig now sees
a real example result instead of an empty page — closing the actual gap the golden script would
have closed, through the path that already exists for this exact situation.

## Config and Environment Changes

None. No new environment variable, no new `Config` field (this iteration's own constant is
explicitly the kind that must NOT become a `Config` field, per this project's long-standing rule
that safety-relevant numeric floors like this one are pinned in code, never adjustable through
configuration).

## Known Limitations

- This entire capability remains invisible in the product today: no button, page, or MCP tool
  triggers it, and no real data has ever passed through it. It only becomes observable once a
  future iteration records real sealed data (explicitly out of scope this round, per this era's
  standing "do not record real tape yet" instruction).
- The one browser-visible proof of this iteration's fix uses a small, clearly-labeled test fixture
  (not real market data) seeded only into a disposable test copy of the backend — it never touches
  real records.
