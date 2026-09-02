## Iteration 0 — goal-observation-contract-iter-0

**Date:** 2026-09-02T23:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: J-01, J-02, J-03, J-04, J-05 (first record — baseline)
- Newly partial: J-06 (first record — era-open documents and the three existing pages pass; the guard test file is absent)
- Regressed: none (no prior state — this is the first iteration of the session)
- Anti-goal violations: none (scan-report CLEAN; ledger totals 0/0/0/0)

**Reasoning:** This was a verify-only baseline and it did exactly that. I confirmed by hand that the
product folders have no changes, that the new machine-readable address `/tape/{ticker}/observation`
is not registered, that `apps/backend/app/observation_contract.py` is missing, and that no
`test_tape_observation_*.py` file exists. The screenshots show the plain "Not Found" body for the
five failing journeys, and the `/desk` page rendering unchanged for J-06. Backend test collection
re-run by me gives 3938 tests, matching the developer and reviewer figures, so the frozen foundation
is intact. Nothing regressed because nothing had passed before.

**Next-step recommendation:** Build the first block of the goal's binding order — the constants, the
builder, the two hash rules and `tests/test_tape_observation_projection.py` for J-01 "the artifact is
a pure projection with identity, provenance and integrity". Keep the web address for later, as the
goal's order requires. Next iteration should be lean, backend-only, with no visible change for users.
