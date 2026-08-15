# goal-referee-iter-10 — Implementation Summary

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Written by:** developer

---

## Features Implemented

- **Referee Adjudications panel on `/desk`**: Below the existing "Referee Registry" panel, a new
  collapsible section shows, for every hypothesis you've registered, its current verdict —
  `registered`, `pending_forward_confirmation`, `insufficient_sample`, `fragile`, `no_evidence`,
  `corroborated`, or `basis_retired` — plus the full paper trail behind it: how many sessions have
  accrued so far, or (once a formal checkpoint exists) the exact evidence hash it was computed
  from, which null and test procedures were used, whether the statistical self-check passed, and
  any fragility warnings. If a checkpoint's own self-check fails, the panel says so plainly and
  refuses to show a confirmatory result rather than pretending everything is fine.
- **Referee Runs panel on `/desk`**: A new panel below Adjudications lets you actually run the
  machinery — build a null baseline for either matched-null procedure, or run a full evaluation for
  any registered hypothesis — with a button, a live progress readout, and a cancel button, plus a
  history table of every past run (when it started/finished, whether it succeeded, and any error).
  If you try to start a second run for the same thing while one is already going, it politely tells
  you it's already running instead of starting a duplicate.
- **Claude connector grows to 22 tools**: The two new panels' data are now readable from a Claude
  conversation too — `desk_referee` and `desk_referee_registry` are new read-only tools, joining
  the 20 that already existed. Nothing on the connector can change any data; it only reads.
- **A promotion-safety gap closed**: Previously, if a champion-promotion certificate were ever
  minted (this still cannot happen through any button or command in the app today — it's a
  developer-only code path with no live callers), it was possible for the certificate to name one
  trading strategy while actually being backed by evidence from a completely different one. That
  loophole is now closed: a certificate can only be minted from evidence that genuinely belongs to
  the strategy it names.

## Changed Behavior

- None. Every existing `/desk` panel, the cockpit page, and the structure page behave exactly as
  before — verified both by an automated scan of the page's own code and by loading the page in a
  real browser.

## Backend-Only Items

- None. Both new panels are wired into the UI; there is no backend capability from this round that
  users cannot see or use through the interface.

## Incomplete Items

- **Full browser screenshot verification** (the three-panel walkthrough with populated example
  data, including one "fragile" example and one "self-check failed" example) is the next pipeline
  step's job (QA), not part of this build step. This handoff documents exactly how to set that
  example data up so QA can do it without guesswork.
- **Nothing else from this round's plan is incomplete.**

## Config and Environment Changes

- None. No new environment variables, config fields, or settings were added. The two new panels
  read the same storage locations the Referee feature already used since earlier rounds.

## Known Limitations

- If a null-build or evaluation run was already in progress before you loaded the page (for
  example, started from another browser tab a moment earlier), the new Runs panel will not
  automatically show it as "running" until you click the button again or re-open the panel. It will
  not start a second, duplicate run — it just won't show the LIVE progress bar for a run it doesn't
  yet know about until the next refresh.
- The "seed identity" line shown in the Adjudications panel's provenance details is the
  hypothesis's own ID, which is the piece of information that actually varies the underlying random
  seed per hypothesis. The raw numeric seed value itself is a fixed constant used everywhere in the
  Referee statistics and isn't something any panel serves as a separate number today.
- Everything from prior rounds (the full statistics engine, the pre-registration registry, the
  starter hypotheses, the promotion safety lock) is untouched and still works exactly as shipped —
  this round only adds the two remaining display panels and closes the one certificate-safety gap
  described above.
