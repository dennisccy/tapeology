# goal-lint report — docs/goal.md

Run: 2026-08-10 · deterministic exit: 0 · semantic findings: 0

## Deterministic lint (goal_lint.py)
clean (exit 0, no output)

An earlier same-day pass on the first draft of the Era B2 goal reported 3
`aspirational-anti-goal` warnings (the "Pre-registration is law" / "Recorded playbook files are
immutable" / "The rail has one owner" bullets led with declarations instead of checkable
prohibitions). The authoring session rephrased all three as veto rules with named guard
mechanisms; the final pass is clean.

## Semantic findings
None.

Checks applied to the Era B2 "The Playbook" goal: journey contradictions (J-01's
measurement-free records vs J-02's additive-disclosure clause are consistent; J-04's
signature re-keying is consistent with J-07's `reused` semantics — reuse holds only at the
current signature); unobservable acceptance (every browser line names visible copy, a section,
or a screenshot; every backend line names a payload, checksum listing, or call-count
assertion); guess-inviting steps (the J-03 date input was pinned to the desk's existing
`validateScreenDayRange` convention during authoring); independent runnability (fixture-scoped
setups per journey; dependency order J-01→J-03 is declared, matching the Era-B precedent);
risky surfaces (the only external call — SPY freshness — rides the existing top-up walk under
the carried explicit-operator-act and no-new-vendor rails); unmeasurable success criteria
(SC-1 carries the verified authoring-time suite count 1926 pass / 8 skip; the others name
observable states). The one deliberate near-duplication — detector journeys J-04/J-05/J-06
sharing the J-03 surface — is a chosen split for iteration size; merging is not advised.

## Summary
Structurally and semantically clean. The goal's highest-leverage property is that every
detector threshold lives in `docs/playbook-detector-spec.md` and re-keys records through the
parameters signature — keep that spec and `docs/goal.md` in lockstep if either is hand-edited
before the era starts (the single highest-impact thing to preserve).
