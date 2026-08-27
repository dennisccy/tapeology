# goal-hypothesis-foundry-iter-7 — Implementation Summary

**Phase:** goal-hypothesis-foundry-iter-7
**Date:** 2026-08-27
**Written by:** developer

---

## Features Implemented

This iteration made **no new user-facing feature**. It is a pure internal bookkeeping repair behind
an already-shipped, unchanged screen. Nothing an operator sees changed.

- **One shared internal calculation now has exactly one home.** A small number the app has been
  showing since last iteration — "how many candidates are ready to run" — was previously worked out
  in two different places inside the code (once in the file that actually feeds the on-screen
  display, and once in a separate one-off script) that happened to agree by coincidence, not by
  design. This iteration moved the calculation the on-screen display actually uses into one clearly
  named, documented function, so there is exactly one place in the changeable part of the codebase
  that owns this number.
- **A permanent automatic check now guards against the two places ever silently disagreeing.** A new
  test loads the real underlying data file, runs the one-off script's formula (copied verbatim, not
  imported, because that script is legally frozen and off-limits for editing — see below) and the
  new shared function side by side, and fails the test suite forever after if they ever produce
  different numbers.

## Changed Behavior

None. The number shown on `/desk` → Hypothesis Foundry → Runner / Checkpoint
("`frozen_ready_total`") is unchanged: it still reads `0`, exactly as before this iteration, because
the underlying real data file still has zero candidates recorded in it. This was verified two ways:
by running the automated test suite, and by starting the real running app and reading the live page
data directly.

## Backend-Only Items

None new — no new endpoint or capability was added.

## Incomplete Items

- **The underlying duplicate calculation still technically exists in the frozen script file.** This
  project has a rule from a previous iteration that a specific batch of 59 files — including the
  one-off script that also does this calculation — is permanently locked and cannot be edited, no
  matter how small the fix, because editing it would break a scientific integrity guarantee the
  project made to itself. That means the "second place doing the same math" cannot be physically
  removed this iteration. What this iteration legally could do — and did — is make sure the
  changeable part of the code has only one true owner, and add a permanent automated check proving
  the frozen script's math still agrees with that owner, so the two can never silently drift apart
  without the test suite catching it immediately.
  A prior automated reviewer step (the "coherence auditor," which checks for exactly this kind of
  duplication) flagged this as a blocking issue last iteration. This iteration's fix may or may not
  fully satisfy that same automated check when it re-runs, because the check may be looking for the
  duplicate calculation to be gone entirely, which — as explained above — is not something this
  iteration is allowed to do. If that check still flags it, the honest next step (already written
  into this iteration's plan ahead of time) is to stop and ask the project owner to make a judgment
  call, not to force a workaround by breaking the file-lock rule.

## Config and Environment Changes

None.

## Known Limitations

- Two things flagged as needing an owner's decision in the previous iteration remain undecided and
  untouched by this iteration, on purpose: (1) every time someone loads the Hypothesis Foundry page,
  the app still quietly writes a small internal bookkeeping file to disk (its fix also lives inside
  a locked file, so it cannot be changed without the same owner sign-off); and (2) an earlier version
  of this research batch was generated and then discarded before this one was finalized, and nobody
  has formally decided whether that discarded version needs any further action. Neither of these
  affects what a user currently sees or does.
- No live external system was touched this iteration (no new adapter, scraper, or third-party API
  call was added), so there is nothing new to spot-check against a real external service.
