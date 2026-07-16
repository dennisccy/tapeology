# goal-lint report — docs/goal.md

Run: 2026-07-17 · deterministic exit: 0 · semantic findings: 1

## Deterministic lint (goal_lint.py)

clean (exit 0, no output)

*(The first pass of this run flagged one warning — `aspirational-anti-goal line 539: anti-goal "**Byte-identity
or it doesn't ship.** Every accelerator lands WITH its determinism/equivalence test" has no checkable
condition` — the line was rewritten as the veto rule "**No divergent accelerator output.** … no accelerator
ships without a passing determinism/equivalence test proving that byte-identity." and the re-run is clean.
Fix applied under the user-approved authoring plan for this session.)*

## Semantic findings

### unobservable-acceptance (page-level budget) — line 466 (pre-fix)

> `page's sections settle within an interactive budget *(operator-verified on the real corpus)*.`

- **Problem:** "settle within an interactive budget" names no number and no visible element — browser-qa and
  the operator have no concrete pass/fail for J-06's page-level outcome.
- **Suggested rewrite:** `every section reaches its ready state (no loading panel remains anywhere on the
  page) within 10 seconds of navigation *(operator-verified on the real corpus)*.`
- **Status:** applied to `docs/goal.md` in this run (user-approved plan). Calibration note: the phrase
  "within an interactive budget" elsewhere (Success Criteria 2, J-01/J-04 acceptance) is always paired with a
  concrete observable (the not-computed payload rendered; a compute-spy proving zero sweep invocations;
  single-flight snapshots) and mirrors the accepted era-5B J-08 house phrasing — not findings.

## Summary

Structurally clean and semantically tight after two in-run fixes: 7 journeys (J-01–J-07) each with concrete
Steps + Acceptance + verifiability tags, an empty `AUTO:journeys` block for the proposer, rails copied
verbatim, all template sections present, measured baselines quoted as ground truth, and the one aspirational
anti-goal now a checkable veto rule. Keyless/operator-verified split is explicit per journey (the real-corpus
timings and the first full real compute are operator acts, never CI gates). Highest-impact next act is not an
edit: start the session — `/goal fast_wall`.
