# Goal Session referee — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting the goal rather than
just reading evidence. The session owner reads this to veto interpretations early.

## iter-0 — goal-evaluator

**Ambiguity:** J-10 "The kept product stands" is written as a continuous regression sentinel, but
its own acceptance also names era-end conditions — screenshots of the three Referee `/desk`
sections and "MCP = exactly 22 tools". At iteration 0 the kept-product half is fully verified
while those two clauses are structurally unmeetable (zero sections exist; 20 tools are
advertised). The goal text does not say whether the sentinel should be scored on its
kept-product half alone or on its whole acceptance.
**We chose:** Scored J-10 `partial`, not `passing`/`already_passing` — the whole-acceptance
reading — and recorded the verified kept-product evidence in `journey-history.json` so no later
iteration re-does that work. Consequence: a future break of the kept product would be caught as a
frozen-foundations anti-goal violation rather than by the `passing → failing` regression rule, and
J-10 closes only when J-09 lands.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-01's acceptance requires the strategy family to carry "the `basis_caveats`
forming-bar disclosure verbatim", but no verbatim text for it exists in `docs/goal.md` or
`docs/referee-statistical-spec.md` — only a description of what it must disclose. So there was
nothing to compare the served sentence against.
**We chose:** Accepted this iteration's first authoring as satisfying "verbatim" — the exported
constant `REFEREE_FORMING_BAR_BASIS_CAVEAT` (`apps/backend/app/research/referee_evidence.py`),
whose served text names `levels._bars_as_of`, the `epoch <= as_of` admission, and the Card 6.4
deferral (screenshot `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png`). It is now the
single source of truth J-06 and J-08 must import rather than re-word. The owner may want to read
that sentence once and edit it now, while only one caller exists.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02's Steps require the playbook adapter to carry a "completeness predicate
(finest-series reach of the RTH close window)" per record, but J-02's own Acceptance list never
names it — the Acceptance names only the two-family goldens, cache parity, pooling/split,
dedup+coverage disclosure, and the SHA-256 no-write listing. The shipped
`session_completeness` is a best-effort estimate derived from `forward.at_utc +
minutes_to_close` (blind to intra-session bar gaps), has zero test assertions, and is not used
as a gate this iteration.
**We chose:** Scored J-02 `passing` against its written Acceptance list, which is fully met and
which I verified myself, rather than withholding the pass for an unlisted Step sub-clause.
Consequence: an untested, admittedly imprecise completeness estimate now exists in the shared
contract, and J-06's confirmatory eligibility (the exploratory/confirmatory separation, a
critical rail) is the first thing that would lean on it. Recorded as a binding rider on the
next iteration instead of a blocker.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** `docs/referee-statistical-spec.md` §2's pseudocode types
`provenance.detector_basis` as a plain string, but a strategy trade has no detector, so the
field has no meaning for that family. goal.md's own Constraints say a developer who finds the
spec unimplementable "DROPS that procedure from the iteration, records the drop, and surfaces
it for an owner ruling — never improvises" (trap T-1).
**We chose:** Accepted the developer's disclosed improvisation — `detector_basis: None` for
every strategy observation, by analogy with `context_algorithm_version`'s explicit
"None when inapplicable" pattern — rather than treating the T-1 deviation as a failure, because
it was surfaced honestly in the handoff and the reviewer's NOTE, it is reversible, and no
consumer exists yet. The owner should either rule on it or codify the exception in the spec
before J-06 builds logic that assumes the field is always populated.
**Reversible:** yes
