# Goal Session rapid-microscope — Assumption Ledger

Append-only. One entry per scoring decision that required interpreting the goal
rather than only reading evidence. Zero entries in an iteration is normal.

## iter-0 — goal-evaluator

**Ambiguity:** J-01 and J-10 each state one combined Acceptance line, but only part of each
was verifiable at era open (J-01's transition documents and era-open baseline; J-10's kept
surfaces, suite, fingerprint and referee hashes). The goal does not say whether partial
satisfaction of a combined acceptance line counts as `failing` or `partial`.
**We chose:** scored both `partial` (browser QA recorded FAIL for the full line), so the
verified sub-checks are not re-done later. `partial` blocks GOAL_ACHIEVED exactly as `failing`
does, so no gate is loosened by this choice.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** `docs/rapid-validation-spec.md` has no dedicated readiness section: it never
defines an RTH-minutes-to-session-equivalents conversion formula, and it never defines a
per-study floor distinct from the three pilot studies goal.md's J-09 names — those studies have
no registered Scout spec yet (that lands in J-09, eight iterations away).
**We chose:** `session_equivalents = rth_minutes_covered / 390` (standard 09:30-16:00 ET RTH
minutes), which reproduces goal.md's own stated ~3.0 on today's corpus; and each of the three
pilot studies reads the SAME existing frozen `WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS`
(=60 sessions) geometry floor from spec §1, since no study-specific floor is spec'd yet and
today's 11 legacy sessions read `floor_unmet` under either reading — matching goal.md's stated
J-01 acceptance ("every pilot study reads `floor_unmet`") regardless.
**Reversible:** yes — J-09 may register a different, study-specific floor later; this reading
only affects a descriptive readiness column, never a gate.
