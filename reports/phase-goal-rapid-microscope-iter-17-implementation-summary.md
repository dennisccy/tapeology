# goal-rapid-microscope-iter-17 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **An automated verdict for sealed-shard evaluations**: previously, when a candidate mechanism's
  sealed (one-time, permanently locked) evidence was evaluated, the pass/fail answer had to be
  supplied by whoever called the code — there was no machinery that actually computed it from the
  data. This round builds that machinery: a new module recomputes the outcome from the underlying
  evidence itself, checks it against a fixed set of pre-agreed rules (enough data, right
  direction, big enough effect, right kind of evidence, the rule hasn't changed since the shard
  was locked in), and only then records a permanent pass, fail, or "not enough data" verdict. This
  closes a gap flagged by the project owner: a verdict that anyone could simply assert is not
  trustworthy for a once-only, unrepeatable evaluation.
- **A trustworthy "earliest safe date" for future confirmation**: the system now computes, for
  any candidate mechanism, the earliest date a genuinely fresh confirmation run could safely
  start — by scanning the ENTIRE history of that mechanism's family (every variant tried,
  including the ones that were killed, not just the winner) for the latest evidence any of them
  ever touched, then adding a safety buffer. Previously this number only looked at the winning
  variant's own evidence, which could be gamed by quietly discarding inconvenient variants that
  had seen more recent data. The corrected version cannot be gamed that way.

## Changed Behavior

- **Sealed-shard evaluation verdicts**: previously, code calling into the graduation ledger had to
  supply a ready-made pass/fail answer as a plain yes/no. That is no longer possible — the answer
  is now always computed by the new dedicated module from the actual underlying evidence. This
  round's only exercise of this new path is on internal test fixtures (no real sealed evidence
  exists yet — the project's Validation Vault has never sealed a real shard), so there is no
  behavior change visible anywhere in the live product today.
- **The "earliest safe confirmation date" number**: this internal, not-yet-displayed number is
  now scanning much more history than before (every attempted variant, not just the winner) and
  building in a safety buffer before recommending a date. It affects nothing rendered on screen or
  reported today — no candidate has reached the stage where this number is used.

## Backend-Only Items

- The whole sealed-evaluation verdict machinery and the corrected "earliest safe confirmation
  date" calculation are backend-only, as they were before this round — they feed an internal
  record-keeping ledger with no dedicated screen. The one place either number could theoretically
  surface (the Desk page's Graduation area) does not exist in the product's navigation yet; this
  round adds no new screen and changes no existing one.

## Incomplete Items

- One of this round's four small side-tasks was to re-run a previously-edited automated
  browser-check script and see if it still passed. It did not — but not because of anything this
  round built. The real, permanent product data behind the "Walk-Forward" panel on the Desk page
  has grown since that check was last written (an earlier round's normal use left a real entry
  there), so the check's old expectation of an empty panel is now stale. The check was left
  exactly as it was rather than being patched around, and the finding is written up for whoever
  updates that check next. This does not remove any working feature — it is a housekeeping item on
  the automated test itself.
- The "earliest safe confirmation date" calculation's final rounding step (finding the next valid
  trading day) currently treats every Monday-through-Friday as valid — it does not yet know about
  stock-market holidays, because no part of this project currently tracks a holiday calendar. This
  makes the number a conservative estimate rather than exact to the day. It is clearly labeled
  as such internally, and it does not affect anything a user can act on today, since the actual
  final gate for any future confirmation remains the separate, untouched adjudication system this
  round does not modify.

## Config and Environment Changes

- None. No new environment variables, no new settings, no schema/config changes of any kind.

## Known Limitations

- The corrected "earliest safe confirmation date" arithmetic (see Incomplete Items) is a
  disclosed estimate, not a calendar-exact one, until a future round adds real market-holiday
  awareness somewhere in the project.
- The re-run browser check (see Incomplete Items) needs a follow-up pass to bring it back in line
  with the current state of the real product data; until then that one automated check will keep
  reporting a mismatch that is a test-data issue, not a product defect.
