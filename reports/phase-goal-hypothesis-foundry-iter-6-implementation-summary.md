# goal-hypothesis-foundry-iter-6 — Implementation Summary

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** developer
**Revision:** updated after the code-review fix pass (2026-08-27) — see the two new items below
and the revised final limitation.

---

## Features Implemented

- **Real exhaust pass**: a new operator command (`run_hypothesis_foundry_real_exhaust.py`) runs the
  Hypothesis Foundry's real, one-time evaluation pass against the already-frozen research plan.
  Because that frozen plan currently contains zero candidate ideas to evaluate (established two
  iterations ago — every source idea this era considered either got blocked for missing scientific
  detail, excluded as previously-decided, or folded into an existing feature), this run completed
  honestly with nothing to test, in well under a second of real work.
- **"Runner / Checkpoint" panel**: `/desk` → Hypothesis Foundry now shows a new section confirming,
  in plain language, that this one-time run happened, when, and that it touched zero pieces of
  protected/sealed research data while doing so.
- **Freeze-record repair**: three small bookkeeping gaps in how the frozen research plan's identity
  is recorded were fixed — the record now works portably across machines, correctly points at the
  exact code version that produced it, and states which evidence category the research is locked to.
- **The QA test rig now sees the real run** (added in the review fix pass): quality checks for this
  product run against a throwaway, sandboxed copy of the app so a test click can never write into
  the operator's real data. That sandbox had no copy of the one-time run's record, so the new panel
  would have truthfully — but misleadingly — reported "not run yet" during every quality check. The
  rig's setup script now copies the real, recorded run log into its sandbox before starting, the
  same way it already copies the era's opening snapshot. If no real run has ever happened, nothing
  is copied and the panel honestly says so; no value is ever invented.

## Changed Behavior

- **None.** Every change this iteration is additive: a new panel section, a new backend field, a
  new operator-run command, and bookkeeping corrections to an internal audit record. No existing
  page, endpoint, or user-visible behavior changed shape.

## Backend-Only Items

- None. The new `exhaust_progress` data is fully wired into the `/desk` UI this same iteration.

## Incomplete Items

- None from this iteration's own scope. (The broader "final Foundry truth" surface — detail
  drill-ins for individual research ideas, survivor labelling, and an optional read-only API-tool
  proxy — is explicitly the NEXT iteration's work, not this one's.)

## Config and Environment Changes

- None. No new environment variables, config fields, or migrations.

## Known Limitations

- The research plan this era produced has **zero candidate ideas to evaluate** — every one of the
  11 source ideas this era was allowed to consider was either scientifically incomplete, already
  decided against in a prior era, or already covered by an existing feature. This is documented as
  a legitimate, honest research outcome by the era's own rules (a sparse or even empty result is an
  acceptable finding, not a failure) — it is not something this iteration can or should "fix" by
  inventing a new candidate.
- The one-time run was not repeated a second time against the full real research-data corpus purely
  to prove it behaves safely if run twice — that would take roughly 13 minutes each time due to the
  corpus's size, and the "safe to run twice" behavior is already proven against a small practice
  copy of the same data plus dedicated internal tests. Re-running it for real remains a safe,
  inexpensive action any time an operator wants to double-check it.
- The automated browser tool returns a blank image when it photographs a section far down a long
  page (a known limitation of this environment's screenshot capture, not a bug in the page). The
  fix pass worked around it by enlarging the browser window so the section fits without scrolling,
  and the new panel is now confirmed by a real screenshot taken through the sandboxed QA rig — the
  panel's on-screen values match the underlying recorded run exactly. Anyone photographing a
  section low on a page in this environment should expect to use the same window-size workaround.
